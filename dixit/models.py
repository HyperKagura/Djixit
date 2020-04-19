from django.db import models
from django.contrib.auth.models import User
import json
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# Create your models here.


class Room(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('date started')

    def __str__(self):
        return self.name

    @property
    def group_id(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return str(self.id)
