import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()

TAG_NAME_MAX_LENGTH = 32
TAG_SLUG_MAX_LENGTH = 32
INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH = 64
RECIPE_NAME_MAX_LENGTH = 256
MIN_VALUE_COOKING_TIME = 1
MAX_VALUE_COOKING_TIME = 32000
MIN_VALUE_INGREDIENT_AMOUNT = 1
MAX_VALUE_INGREDIENT_AMOUNT = 32000
SHORT_CODE_URLS_MAX_LENGTH = 3


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(to=Tag, verbose_name='Тэг')
    author = models.ForeignKey(
        to=User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='RecipeIngredient'
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=RECIPE_NAME_MAX_LENGTH
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='images'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(
                MIN_VALUE_COOKING_TIME,
                message=('Время приготовления не может быть меньше '
                         f'{MIN_VALUE_COOKING_TIME}!')
            ),
            MaxValueValidator(
                MAX_VALUE_COOKING_TIME,
                message=('Время приготовления не может быть больше '
                         f'{MAX_VALUE_COOKING_TIME}!')
            )
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_code = models.CharField(
        max_length=SHORT_CODE_URLS_MAX_LENGTH,
        verbose_name='Короткий код',
        unique=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('pub_date',)

    def generate_short_code(self):
        while True:
            code = ''.join(
                random.choices(
                    settings.CHARACTERS,
                    k=SHORT_CODE_URLS_MAX_LENGTH
                )
            )
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_short_code()
        super().save(*args, **kwargs)

    @property
    def favorites_count(self):
        return self.favorites.count()

    def __str__(self):
        return f'{self.name} пользователя "{self.author}"'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        related_name='ingredient_recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_VALUE_INGREDIENT_AMOUNT,
                message=('Количество ингредиента не может быть меньше '
                         f'{MIN_VALUE_INGREDIENT_AMOUNT}!')
            ),
            MaxValueValidator(
                MAX_VALUE_INGREDIENT_AMOUNT,
                message=('Количество ингредиента не должно превышать '
                         f'{MAX_VALUE_INGREDIENT_AMOUNT}!')
            )
        ]
    )


class UserRecipeModel(models.Model):
    user = models.ForeignKey(
        to=User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        to=Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        default_related_name = '%(class)ss'
        ordering = ('user',)
        abstract = True

    def __str__(self):
        return f'{self.recipe} в {self._meta.verbose_name} у {self.user}'


class Favorite(UserRecipeModel):
    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeModel):
    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
