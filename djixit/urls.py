"""djixit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import include, path, re_path
from .views import HomeView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#import .settings
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dixit/', include('dixit.urls')),
    path('cah/', include('cah.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^login/$', LoginView.as_view()),
    re_path(r'^logout/$', LogoutView.as_view()),
    re_path(r'^change_password/$', PasswordChangeView.as_view()),

    re_path(r'^$', HomeView.as_view())
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
