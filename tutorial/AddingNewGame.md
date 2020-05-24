#Adding New Game

```shell script
python manage.py startapp myGame
```

add your app to installed apps in djixit.settings.py

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # this is first app
    'dixit.apps.DixitConfig',      # this is second app
    'cah.apps.CahConfig',
    'channels',
]
```


add routing for websocket in djixit/routing.py. Example for 2 apps:

```python
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            dixit.routing.websocket_urlpatterns +  # for first app
            cah.routing.websocket_urlpatterns      # for second app
        )
    ),
})
```

To edit your new models from admin GUI register them in mygame/admin.py . For example:

```python
# Register your models here.
from .models import CahRoom, CahUsersInRoom, CahCardSet, CahCard, CahCardGame, CahRoomCardSet

admin.site.register(CahRoom)
admin.site.register(CahUsersInRoom)
admin.site.register(CahCardSet)
admin.site.register(CahCard)
admin.site.register(CahCardGame)
admin.site.register(CahRoomCardSet)

```