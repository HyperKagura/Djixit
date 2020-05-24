from django.contrib import admin

# Register your models here.
from .models import CahRoom, CahUsersInRoom, CahCardSet, CahCard, CahCardGame, CahRoomCardSet

admin.site.register(CahRoom)
admin.site.register(CahUsersInRoom)
admin.site.register(CahCardSet)
admin.site.register(CahCard)
admin.site.register(CahCardGame)
admin.site.register(CahRoomCardSet)
