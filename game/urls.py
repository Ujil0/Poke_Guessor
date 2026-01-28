from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/start-game/', views.start_game, name='start_game'),
    path('api/guess/', views.guess_pokemon, name='guess_pokemon'),
    path('api/autocomplete/', views.autocomplete, name='autocomplete'),
    path('api/stats/', views.get_stats, name='get_stats'),
    path('api/settings/', views.get_settings, name='get_settings'),
    path('api/settings/update/', views.update_settings, name='update_settings'),
]
