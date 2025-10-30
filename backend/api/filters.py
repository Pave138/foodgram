from django_filters.rest_framework import (
    FilterSet, AllValuesMultipleFilter, BooleanFilter)

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart')
    tags = AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')
