from django.contrib import admin
from django.urls import include, path

from api.views import redirect_to_recipe

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<slug:recipe_short_code>/',
        redirect_to_recipe,
        name='redirect_to_recipe'
    )
]
