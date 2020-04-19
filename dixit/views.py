from django.views.generic import DetailView, ListView
from .models import Room
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'dixit/home.html'


class RoomView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/room.html'
    model = Room
