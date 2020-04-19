from django.db import models
from django.contrib.auth.models import User
import json
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# Create your models here.

ROOM_CONNECTIONS_LIMIT = 2


class Room(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('date started')
    connections_number = models.IntegerField(default=0)
    is_full = None

    def __init__(self, *args, **kwargs):
        super(Room, self).__init__(*args, **kwargs)
        self.is_full = self.full()

    def __str__(self):
        return self.name

    @property
    def group_id(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return str(self.id)

    def add_connection(self):
        self.connections_number += 1
        self.save()
        self.is_full = self.full()

    def remove_connection(self):
        self.connections_number -= 1
        self.save()
        self.is_full = self.full()

    def full(self):
        return self.connections_number >= ROOM_CONNECTIONS_LIMIT
