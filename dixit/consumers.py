import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels import auth
from django.contrib.auth.models import User
from .models import Room


class ChatConsumer(AsyncWebsocketConsumer):
    room_name = None
    room_group_name = None
    room = None
    user = None
    user_in_room = None

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = 'chat_%s' % self.room_name
        self.room = await sync_to_async(Room.objects.get)(id=self.room_name)
        self.user = await auth.get_user(self.scope)

        if self.room.full():
            await self.close()
        else:
            self.user_in_room = await sync_to_async(self.room.add_connection)(self.user)
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'connections_changed',
                    'current_number': self.room.connections_number,
                    'user_connected': str(self.user),
                }
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await sync_to_async(self.user_in_room.delete)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'connections_changed',
                'current_number': self.room.connections_number,
                'user_disconnected': str(self.user),
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'from_user': str(self.user),
            }
        )

    # Receive change of connections
    async def connections_changed(self, event):
        num = event['current_number']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'connections_changed',
            'current_number': num

        }))

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'from_user': event['from_user'],
        }))
