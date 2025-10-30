from django.contrib import admin

from .models import Ingredient, Recipe, Tag, Favorite, ShoppingCart

COUNT_PER_PAGE = 20


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    list_display_links = ('name',)
    list_per_page = COUNT_PER_PAGE


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    list_per_page = COUNT_PER_PAGE


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('author', 'name',)
    list_filter = ('tags',)
    list_display_links = ('author', 'name')
    readonly_fields = ('get_favorites_count_display',)

    def get_favorites_count_display(self, obj):
        count = obj.favorites_count
        return f'Этот рецепт добавлен в избранное {count} раз(а)'

    get_favorites_count_display.short_description = 'Статистика избранного'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)
    list_per_page = COUNT_PER_PAGE


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)
    list_per_page = COUNT_PER_PAGE
