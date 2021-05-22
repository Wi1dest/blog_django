from django.urls import path

from home.views import HomeView
from users.views import RegisterView

urlpatterns = [
    path('index',HomeView.as_view(),name = 'index'),
]