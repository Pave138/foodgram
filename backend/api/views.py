from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .pagination import FoodgramApiPagination
from .serializers import (
    SubscriptionUserReadSerializer, SubscriptionUserWriteSerializer,
    UserAvatarSerializer, FavoriteSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, TagSerializer,
    ShoppingCartSerializer)
from recipes.models import (
    Favorite, Ingredient, Recipe, Tag, ShoppingCart, RecipeIngredient)
from users.models import Subscription

User = get_user_model()


def redirect_to_recipe(request, recipe_short_code):
    recipe = Recipe.objects.get(short_code=recipe_short_code)
    return HttpResponseRedirect(
        request.build_absolute_uri(
            f'/recipes/{recipe.id}/'
        )
    )


class FoodgramUserViewSet(UserViewSet):
    pagination_class = FoodgramApiPagination

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        return super().me(request)

    @action(
        methods=('put',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        followings = User.objects.filter(followings__user=user)
        pagination = self.paginate_queryset(followings)
        serializer = SubscriptionUserReadSerializer(
            pagination,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        data = {
            'user': request.user.id,
            'following': author.id
        }
        serializer = SubscriptionUserWriteSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        count_delete_subscribe, _ = Subscription.objects.filter(
            user=user, following=author
        ).delete()
        if not count_delete_subscribe:
            return Response(
                f'Вы не были подписаны на пользователя {author.username}!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            f'Вы отписались от пользователя {author.username}!',
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    pagination_class = FoodgramApiPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        user_id = user.id if not user.is_anonymous else None
        return Recipe.objects.all().select_related('author',).prefetch_related(
            'tags', 'ingredients'
        ).annotate(
            total_favorited=models.Count(
                'favorites',
                distinct=True,
                filter=models.Q(favorites__user_id=user_id)
            ),
            is_favorited=models.Case(
                models.When(total_favorited__gte=1, then=True),
                default=False,
                output_field=models.BooleanField()
            ),
            recipe_in_shopping_cart=models.Count(
                'shoppingcarts',
                filter=models.Q(shoppingcarts__user_id=user_id)
            ),
            is_in_shopping_cart=models.Case(
                models.When(recipe_in_shopping_cart__gte=1, then=True),
                default=False,
                output_field=models.BooleanField()
            )
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        methods=('get',),
        detail=True,
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        relative_url = reverse('redirect_to_recipe', args=[recipe.short_code])
        full_url = request.build_absolute_uri(relative_url)

        return Response({'short-link': full_url}, status=status.HTTP_200_OK)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        count_delete_recipe, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not count_delete_recipe:
            return Response(
                'Рецепт в списке покупок не найден!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            amounts=Sum('amount')
        )
        file = f'Список ингредиентов пользователя {user.username}:\n'
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            meas_unit = ingredient['ingredient__measurement_unit']
            amounts = ingredient['amounts']
            file += f'    • {name.capitalize()} - {amounts} {meas_unit};\n'

        file += '\nwww.foodrgram.ddns.net'
        response = HttpResponse(file, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = f'attachment; filename="Ингредиенты {user.username}.txt"'
        return response

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        count_delete_favorite, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not count_delete_favorite:
            return Response(
                'Рецепт в избранном не найден!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
