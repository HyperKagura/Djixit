import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels import auth
from .models import CahRoom, CahUsersInRoom, CahCardGame, CahCardVotes
from .models import ROOM_GAME_STATE_WAITING_PLAYERS, ROOM_GAME_STATE_OTHER_PICK_CARD, ROOM_GAME_STATE_VOTING
from .models import CARD_STATE_VOTE, CARD_STATE_IN_GAME, CARD_STATE_VOTE_PREV, CARD_STATE_WAITING
from .models import CARD_TYPE_ANSWER, CARD_TYPE_QUESTION
import random


class ChatConsumer(AsyncWebsocketConsumer):
    room_name = None
    room_group_name = None
    room = None
    user = None
    user_in_room = None

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = 'chat_%s' % self.room_name
        self.room = await sync_to_async(CahRoom.objects.get)(id=self.room_name)
        self.user = await auth.get_user(self.scope)
        try:
            self.user_in_room = await sync_to_async(CahUsersInRoom.objects.get)(room=self.room, user=self.user)
        except Exception as e:
            self.user_in_room = None
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        #await self.channel_layer.group_send(
        #    self.room_group_name,
        #    {
        #        'type': 'connections_changed',
        #        'current_number': self.room.connections_number,
        #        'user_connected': str(self.user),
        #    }
        #)
        await self.game_state_changed({"game_state": self.room.game_state})
        await self.build_stats_message()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        #await self.channel_layer.group_send(
        #    self.room_group_name,
        #    {
        #        'type': 'connections_changed',
        #        'current_number': self.room.connections_number,
        #        'user_disconnected': str(self.user),
        #    }
        #)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == 'game-event':
            question = None
            try:
                self.user_in_room = await sync_to_async(CahUsersInRoom.objects.get)(room=self.room, user=self.user)
                question_card = await sync_to_async(CahCardGame.objects.filter)(room=self.room,
                                                                                card__card_type=CARD_TYPE_QUESTION,
                                                                                card_state=CARD_STATE_VOTE)
                question = await sync_to_async(lambda card_filter: card_filter[0].card.path())(question_card)
            except CahUsersInRoom.DoesNotExist as e:
                self.user_in_room = None
                return
            if text_data_json['game-event'] == 'choice':
                print("choice: ", text_data_json['choice'])
                if not self.user_in_room.is_host and self.user_in_room.action_required:
                    print("choice card_id is: {}".format(text_data_json['choice']))
                    await sync_to_async(self.set_choice_card)(int(text_data_json['choice']))
                    card_query = await sync_to_async(CahCardGame.objects.filter)(room=self.room, user=self.user_in_room,
                                                                              card_state=CARD_STATE_IN_GAME)
                    card_set = await sync_to_async(lambda card_query: [
                        {"id": card.id, "path": card.card.path(), "my": card.user.id == self.user_in_room.id} for card
                        in
                        card_query])(card_query)
                    await self.send_msg_to_user("waiting for other players to choose a card", "game")
                    await self.send_state_to_user("choice", False, card_set, question,
                                                      action_required=False)
            elif text_data_json['game-event'] == 'vote':
                if self.user_in_room.is_host and self.user_in_room.action_required:
                    print("vote card_id is: {}".format(text_data_json['choice']))
                    await sync_to_async(self.set_vote_card)(int(text_data_json['choice']))
                    card_query = await sync_to_async(CahCardGame.objects.filter)(room=self.room,
                                                                              card_state=CARD_STATE_VOTE,
                                                                                 card__card_type=CARD_TYPE_ANSWER)
                    card_set = await sync_to_async(
                            lambda card_query: [
                                {"id": card.id, "path": card.card.path(), "my": card.user.id == self.user_in_room.id}
                                for card in card_query])(card_query)
                    await self.send_msg_to_user("waiting for other players to vote", "game")
                    await self.send_state_to_user("vote", False, card_set, question,
                                                          action_required=False)
        elif text_data_json['type'] == 'message':
            message = text_data_json['message']
            try:
                self.user_in_room = await sync_to_async(CahUsersInRoom.objects.get)(room=self.room, user=self.user)
            except CahUsersInRoom.DoesNotExist as e:
                self.user_in_room = None
                return

            if self.user_in_room:
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
    #async def connections_changed(self, event):
    #    num = event['current_number']
#
#        # Send message to WebSocket
#        await self.send(text_data=json.dumps({
#            'type': 'connections_changed',
#            'current_number': num
#
#        }))

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

    async def send_state_to_user(self, state, is_host, card_set, question, is_observer=False, action_required=False):
        await self.send(text_data=json.dumps({
            'type': 'state_update',
            'state': state,
            'is_host': is_host,
            'is_observer': is_observer,
            'card_set': card_set,
            'question': question,
            'action_required': action_required
        }))

    async def game_stats_changed(self, event):
        print("game_stats_changed")
        await self.build_stats_message()

    async def game_state_changed(self, event):
        game_state = event["game_state"]
        await self.update_models()
        if game_state == ROOM_GAME_STATE_VOTING:
            print("ROOM_GAME_STATE_VOTING")
            await self.build_voting_message()
        elif game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
            print("ROOM_GAME_STATE_OTHER_PICK_CARD")
            await self.build_choice_message()
        elif game_state == ROOM_GAME_STATE_WAITING_PLAYERS:
            await self.send_state_to_user("wait", False, [], None)
            await self.send_msg_to_user("waiting for players", "game")

    def set_choice_card(self, card_id):
        try:
            card = CahCardGame.objects.get(id=card_id, user=self.user_in_room)
            card.card_state = CARD_STATE_VOTE
            card.save()
            self.user_in_room.action_required = False
            self.user_in_room.save()
            print("user choice change")
        except Exception as e:
            print(e)

    def set_vote_card(self, card_id):
        try:
            card = CahCardGame.objects.get(id=card_id)
            CahCardVotes.objects.create(card=card, user=self.user_in_room, room=self.room)
            self.user_in_room.action_required = False
            self.user_in_room.save()
            print("user vote change")
        except Exception as e:
            print(e)

    def get_host_name(self):
        try:
            return str(CahUsersInRoom.objects.filter(room=self.room, is_host=True)[0].user)
        except Exception as e:
            print(e)
            return "Guru"

    def get_card_votes(self):
        cards = CahCardGame.objects.filter(room=self.room, card_state=CARD_STATE_VOTE_PREV)
        return [{"id": card.id, "path": card.card.path(), "host": card.hosts_card, "users": [str(vote.user.user) for vote in CahCardVotes.objects.filter(card=card)]} for card in cards]

    async def build_voting_message(self):
        card_query = await sync_to_async(CahCardGame.objects.filter)(room=self.room, card_state=CARD_STATE_VOTE, card__card_type=CARD_TYPE_ANSWER)
        question_card = await sync_to_async(CahCardGame.objects.filter)(room=self.room,
                                                                        card__card_type=CARD_TYPE_QUESTION,
                                                                        card_state=CARD_STATE_VOTE)
        question = await sync_to_async(lambda card_filter: card_filter[0].card.path())(question_card)
        if not self.user_in_room:
            card_set = await sync_to_async(
                lambda card_query: [{"id": card.id, "path": card.card.path(), "my": False}
                                    for card in card_query])(card_query)
            random.shuffle(card_set)
            print("anonim")
            await self.send_msg_to_user("waiting for other players to vote", "game")
            await self.send_state_to_user("vote", False, card_set, question, True)
        else:
            card_set = await sync_to_async(
                lambda card_query: [
                    {"id": card.id, "path": card.card.path(), "my": card.user.id == self.user_in_room.id}
                    for card in card_query])(card_query)
            random.shuffle(card_set)
            if self.user_in_room.is_host:
                print("host")
                await self.send_msg_to_user("vote for the card", "game")
                await self.send_state_to_user("vote", True, card_set, question,
                                              action_required=self.user_in_room.action_required)
            else:
                print("non-host")
                await self.send_msg_to_user("waiting for host to vote", "game")
                await self.send_state_to_user("vote", False, card_set, question)

    async def build_choice_message(self):
        question_card = await sync_to_async(CahCardGame.objects.filter)(room=self.room,
                                                                        card__card_type=CARD_TYPE_QUESTION,
                                                                        card_state=CARD_STATE_VOTE)
        question = await sync_to_async(lambda card_filter: card_filter[0].card.path())(question_card)
        self.room = await sync_to_async(CahRoom.objects.get)(id=self.room_name)
        if not self.user_in_room:
            print("anonim")
            await self.send_msg_to_user("waiting for other players to choose a card", "game")
            await self.send_state_to_user("choice", False, [], question, True)
        else:
            card_query = await sync_to_async(CahCardGame.objects.filter)(room=self.room, user=self.user_in_room, card__card_type=CARD_TYPE_ANSWER,
                                                                      card_state=CARD_STATE_IN_GAME)
            card_set = await sync_to_async(lambda card_query: [
                {"id": card.id, "path": card.card.path(), "my": card.user.id == self.user_in_room.id} for card in
                card_query])(card_query)
            print("question is", question)
            if (self.user_in_room is None) or self.user_in_room.is_host:
                print("anonim or host")
                await self.send_msg_to_user("waiting for other players to choose a card", "game")
                await self.send_state_to_user("choice", True, card_set, question)
            else:
                print("non-host")
                await self.send_msg_to_user("choose a card", "game")
                await self.send_state_to_user("choice", False, card_set, question,
                                              action_required=self.user_in_room.action_required)

    async def build_stats_message(self):
        stats = await sync_to_async(
            lambda user_query: [{"name": str(user.user), "score": user.score, "round": user.round_score} for user in
                                user_query])(
            CahUsersInRoom.objects.filter(room=self.room))
        card_votes = await sync_to_async(self.get_card_votes)()
        cards_left = await sync_to_async(CahCardGame.objects.filter(room=self.room, card_state=CARD_STATE_WAITING).count)()
        print(stats)
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'scores': stats,
            'card_set': card_votes,
            'stack': cards_left
        }))

    async def update_models(self):
        try:
            self.user_in_room = await sync_to_async(CahUsersInRoom.objects.get)(room=self.room, user=self.user)
        except Exception as e:
            self.user_in_room = None
        self.room = await sync_to_async(CahRoom.objects.get)(id=self.room_name)
