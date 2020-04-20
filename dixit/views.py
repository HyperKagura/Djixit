from django.views.generic import DetailView, ListView
from .models import Room, UsersInRoom
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'dixit/home.html'


class RoomView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/room.html'
    model = Room

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_in_room"] = UsersInRoom.objects.filter(user=self.request.user).count()
        return context
