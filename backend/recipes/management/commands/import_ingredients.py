import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'pass'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', default='data/ingredients.json',
            help='Путь до JSON с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / options['file']

        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Ошибка: Файл {file_path} не найден')
            )
            return
        self.stdout.write(
            self.style.SUCCESS(f'Загрузка ингредиентов с {file_path}...')
        )

        with open(file_path, encoding='utf-8') as f:
            ingredients_data = json.load(f)
        try:
            with transaction.atomic():
                for ingredient in ingredients_data:
                    Ingredient.objects.create(
                        name=ingredient['name'],
                        measurement_unit=ingredient['measurement_unit']
                    )
        except IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                self.stdout.write(
                    self.style.ERROR('Ингредиенты уже существуют')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('Импорт завершен')
            )
