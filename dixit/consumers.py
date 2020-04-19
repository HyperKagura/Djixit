import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels import auth
from django.contrib.auth.models import User
from .models import Room, UsersInRoom
from .models import ROOM_GAME_STATE_WAITING_PLAYERS, ROOM_GAME_STATE_HOST_PICKS_CARD, ROOM_GAME_STATE_OTHER_PICK_CARD, ROOM_GAME_STATE_ROUND_RESULT, ROOM_GAME_STATE_VOTING


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
        try:
            self.user_in_room = await sync_to_async(UsersInRoom.objects.get)(room=self.room, user=self.user)
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
        except UsersInRoom.DoesNotExist as e:
            print("connecting")
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
        await self.send_msg_to_user(message, event['from_user'])

    async def send_msg_to_user(self, msg, from_field):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': msg,
            'from_user': from_field,
        }))

    async def game_state_changed(self, event):
        game_state = event["game_state"]
        if game_state == ROOM_GAME_STATE_HOST_PICKS_CARD:
            if self.user_in_room.is_host:
                await self.send_msg_to_user("you are the host, choose a card", "game")
            else:
                await self.send_msg_to_user("waiting for host to choose a card", "game")
        elif game_state == ROOM_GAME_STATE_VOTING:
            if self.user_in_room.is_host:
                await self.send_msg_to_user("waiting for other players to choose a card", "game")
            else:
                await self.send_msg_to_user("choose a card", "game")

