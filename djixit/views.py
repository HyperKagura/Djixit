from django.views.generic import CreateView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login


class HomeView(TemplateView):
    template_name = 'home.html'

