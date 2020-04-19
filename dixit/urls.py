from django.urls import re_path, path
from .views import HomeView, RoomView

urlpatterns = [
    re_path(r'^$', HomeView.as_view()),
    path('<int:pk>/', RoomView.as_view()),
]
