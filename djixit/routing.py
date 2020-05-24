from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import dixit.routing
import cah.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            dixit.routing.websocket_urlpatterns +
            cah.routing.websocket_urlpatterns
        )
    ),
})
