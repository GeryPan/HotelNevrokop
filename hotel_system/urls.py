from django.urls import path
from . import views

urlpatterns = [
    # Route for the main home page
    path('', views.home, name='home'),
]