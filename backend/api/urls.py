from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers

from .views import (
    FoodgramUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet)

api_v1 = routers.DefaultRouter()
api_v1.register('users', FoodgramUserViewSet, basename='users')
api_v1.register('recipes', RecipeViewSet, basename='recipes')
api_v1.register('tags', TagViewSet, basename='tags')
api_v1.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
] + api_v1.urls

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
