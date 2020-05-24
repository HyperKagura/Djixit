from django.views.generic import DetailView, ListView
from .models import CahRoom, CahUsersInRoom
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin, ListView):
    model = CahRoom
    template_name = 'cah/home.html'


class RoomView(DetailView):
    template_name = 'cah/room.html'
    model = CahRoom

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        try:
            context["user_in_room"] = CahUsersInRoom.objects.filter(user=self.request.user, room=room).count()
            print("user {} count is: {}".format(self.request.user, context["user_in_room"]))
        except:
            context["user_in_room"] = 0
        return context

    def get_object(self):
        obj = super().get_object()
        obj.waiting_players = obj.is_waiting()
        return obj


class JoinRoomView(LoginRequiredMixin, DetailView):
    template_name = 'cah/join_room.html'
    model = CahRoom

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = CahUsersInRoom.objects.filter(user=self.request.user, room=room).count()
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
    template_name = 'cah/leave_room.html'
    model = CahRoom

    def get_context_data(self, **kwargs):
        room = super().get_object()
        CahUsersInRoom.objects.filter(user=self.request.user, room=room).delete()
        context = super().get_context_data(**kwargs)
        return context


class StartGameView(LoginRequiredMixin, DetailView):
    template_name = 'cah/start_game.html'
    model = CahRoom

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = CahUsersInRoom.objects.filter(user=self.request.user, room=room).count()
        context["user_in_room"] = user_in_room
        if user_in_room:
            room.start_game()
        return context


class StopGameView(LoginRequiredMixin, DetailView):
    template_name = 'cah/stop_game.html'
    model = CahRoom

    def get_context_data(self, **kwargs):
        room = super().get_object()
        context = super().get_context_data(**kwargs)
        user_in_room = CahUsersInRoom.objects.filter(user=self.request.user, room=room).count()
        context["user_in_room"] = user_in_room
        if user_in_room:
            room.stop_game()
        return context
