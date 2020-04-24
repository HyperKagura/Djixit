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
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        context["user_in_room"] = UsersInRoom.objects.filter(user=self.request.user, room=room).count()
        print("user {} count is: {}".format(self.request.user, context["user_in_room"]))
        return context

    def get_object(self):
        obj = super().get_object()
        obj.waiting_players = obj.is_waiting()
        return obj


class JoinRoomView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/join_room.html'
    model = Room

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = UsersInRoom.objects.filter(user=self.request.user, room=room).count()
        if user_in_room:
            context["room_is_full"] = False
            return context
        else:
            if room.is_full:
                context["room_is_full"] = True
            else:
                room.add_connection(self.request.user)
                context["room_is_full"] = False
        return context


class LeaveRoomView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/leave_room.html'
    model = Room

    def get_context_data(self, **kwargs):
        room = super().get_object()
        UsersInRoom.objects.filter(user=self.request.user, room=room).delete()
        context = super().get_context_data(**kwargs)
        return context


class StartGameView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/start_game.html'
    model = Room

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = UsersInRoom.objects.filter(user=self.request.user, room=room).count()
        context["user_in_room"] = user_in_room
        if user_in_room:
            room.start_game()
        return context


class StopGameView(LoginRequiredMixin, DetailView):
    template_name = 'dixit/stop_game.html'
    model = Room

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = UsersInRoom.objects.filter(user=self.request.user, room=room).count()
        context["user_in_room"] = user_in_room
        if user_in_room:
            room.stop_game()
        return context



