from django.contrib import admin

# Register your models here.
from .models import Room, CardSet, Card, CardGame, RoomCardSet

admin.site.register(Room)
admin.site.register(CardSet)
admin.site.register(Card)
admin.site.register(CardGame)
admin.site.register(RoomCardSet)
