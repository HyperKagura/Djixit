from django.urls import re_path, path
from .views import HomeView, RoomView, JoinRoomView, LeaveRoomView, StartGameView, StopGameView

urlpatterns = [
    re_path(r'^$', HomeView.as_view()),
    path('<int:pk>/', RoomView.as_view()),
    path('<int:pk>/leave', LeaveRoomView.as_view()),
    path('<int:pk>/join', JoinRoomView.as_view()),
    path('<int:pk>/start', StartGameView.as_view()),
    path('<int:pk>/stop', StopGameView.as_view()),
]