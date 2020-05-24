from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random

# Create your models here.

ROOM_GAME_STATE_WAITING_PLAYERS = 0
ROOM_GAME_STATE_OTHER_PICK_CARD = 1
ROOM_GAME_STATE_VOTING = 2
#ROOM_GAME_STATE_ROUND_RESULT = 4


class CahRoom(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('date started', auto_now_add=True)
    connections_number = models.IntegerField(default=0)
    game_state = models.IntegerField(default=0, null=False)
    prev_game_state = models.IntegerField(default=0, editable=False, null=False)
    num_people_action_needed = models.IntegerField(default=0, null=False)
    is_full = models.BooleanField(default=False, null=False)
    max_players = models.IntegerField(default=7, null=False)

    def __init__(self, *args, **kwargs):
        super(CahRoom, self).__init__(*args, **kwargs)
        self.is_full = self.full()
        self.prev_game_state = self.game_state
        self.save()

    def __str__(self):
        return self.name

    @property
    def group_id(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return str(self.id)

    def add_connection(self, user):
        user_in_room = CahUsersInRoom.objects.create(user=user, room=self)
        self.connections_number = CahUsersInRoom.objects.filter(room=self).count()
        self.is_full = self.full()
        self.save()
        #async_to_sync(get_channel_layer().group_send)(
        #    "chat_" + str(self.id),
        #    {
        #        'type': 'connections_changed',
        #        'current_number': self.connections_number
        #    }
        #)
        return user_in_room

    def start_game(self):
        self.game_state = ROOM_GAME_STATE_OTHER_PICK_CARD
        self.save()

    def stop_game(self):
        self.game_state = ROOM_GAME_STATE_WAITING_PLAYERS
        self.save()

    def full(self):
        return self.connections_number >= self.max_players

    def is_waiting(self):
        return self.game_state == ROOM_GAME_STATE_WAITING_PLAYERS


class CahUsersInRoom(models.Model):
    room = models.ForeignKey(CahRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_host = models.BooleanField(default=False, null=False)
    score = models.IntegerField(default=0, null=False)
    round_score = models.IntegerField(default=0, null=False)
    is_online = models.BooleanField(default=False, null=False)
    action_required = models.BooleanField(default=False, null=False)
    prev_action_required = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = ["room", "user"]

    def __str__(self):
        return str(self.room) + ": " + str(self.user) + "-" + str(self.id)

    def set_host(self):
        CahUsersInRoom.objects.filter(room=self.room).update(is_host=False)
        self.is_host = True
        self.action_required = True
        self.save()

    def set_next_host(self):
        if self.is_host:
            next_hosts = CahUsersInRoom.objects.filter(room=self.room, id__gt=self.id).order_by("id")
            if len(next_hosts) == 0:  # set first user in room to be host
                print("no hosts after")
                next_hosts = CahUsersInRoom.objects.filter(room=self.room).order_by("id")
                print(next_hosts)
                if len(next_hosts) == 0:  # set first user in room to be host
                    print("error: no users left in room")
                    return
            print("next host is" + str(next_hosts[0]))
            next_hosts[0].set_host()


class CahCardSet(models.Model):
    name = models.CharField(max_length=200)
    answer_cards_number = models.IntegerField(default=0)
    question_cards_number = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class CahRoomCardSet(models.Model):
    set = models.ForeignKey(CahCardSet, on_delete=models.CASCADE)
    room = models.ForeignKey(CahRoom, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["room_id", "set_id"]

    def __str__(self):
        room_name = self.room.name
        card_set = self.set.name
        return room_name + ": " + card_set


CARD_TYPE_QUESTION = 0
CARD_TYPE_ANSWER = 1


class CahCard(models.Model):
    set = models.ForeignKey(CahCardSet, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default="", null=False)
    card_type = models.IntegerField(default=0, null=False)
    num_fields = models.IntegerField(default=1, null=False)

    class Meta:
        unique_together = ["set", "name"]

    def __str__(self):
        return "card" + self.name

    def path(self):
        sup_path = "black/" if self.card_type == CARD_TYPE_QUESTION else "white/"
        return self.set.name + "/card" + self.name + ".png"


CARD_STATE_WAITING = 0
CARD_STATE_IN_GAME = 1
CARD_STATE_PLAYED = 2
CARD_STATE_VOTE = 3
CARD_STATE_VOTE_PREV = 4


class CahCardGame(models.Model):
    card = models.ForeignKey(CahCard, on_delete=models.CASCADE)
    room = models.ForeignKey(CahRoom, on_delete=models.CASCADE)
    card_set = models.ForeignKey(CahCardSet, on_delete=models.CASCADE)
    card_state = models.IntegerField(default=0, null=False)  # 0 - waiting, 1 - in use
    user = models.ForeignKey(CahUsersInRoom, null=True, on_delete=models.SET_NULL)
    hosts_card = models.BooleanField(default=False, null=False)  # set to True when host picks this card

    class Meta:
        unique_together = ["card", "room", "card_set"]

    def __str__(self):
        return str(self.room) + ": " + str(self.card_set) + " " + str(self.card)

    def set_user(self, user_id):
        self.card_state = CARD_STATE_IN_GAME
        self.user_id = user_id
        self.save()

    def set_state_waiting(self):
        self.card_state = CARD_STATE_WAITING
        self.user_id = None
        self.save()

    def set_state_vote(self):
        self.card_state = CARD_STATE_VOTE
        self.save()

    def set_state_played(self):
        self.card_state = CARD_STATE_PLAYED
        self.save()


class CahCardVotes(models.Model):
    user = models.ForeignKey(CahUsersInRoom, on_delete=models.CASCADE)
    card = models.ForeignKey(CahCardGame, on_delete=models.CASCADE)
    room = models.ForeignKey(CahRoom, on_delete=models.CASCADE)


@receiver(models.signals.post_save, sender=CahRoomCardSet)
def add_cards_to_game(instance, created, raw, **kwargs):
    if created:
        cards = CahCard.objects.filter(set=instance.set)
        for card in cards:
            CahCardGame.objects.create(card=card, room=instance.room, card_set=instance.set, card_state=CARD_STATE_WAITING)


@receiver(models.signals.post_save, sender=CahCardSet)
def create_cards_in_set(instance, created, raw, **kwargs):
    if created:
        for i in range(instance.answer_cards_number):
            CahCard.objects.create(set=instance, name=str(i+1), card_type=CARD_TYPE_ANSWER)
        for i in range(instance.question_cards_number):
            CahCard.objects.create(set=instance, name=str(i+1), card_type=CARD_TYPE_QUESTION)


@receiver(models.signals.pre_delete, sender=CahRoomCardSet)
def remove_cards_from_game(instance, using, **kwargs):
    CahCardGame.objects.filter(card_set=instance.set, room=instance.room).delete()


@receiver(models.signals.pre_delete, sender=CahUsersInRoom)
def change_user_count_pre(instance, using, **kwargs):
    if instance.is_host:
        instance.set_next_host()


@receiver(models.signals.post_delete, sender=CahUsersInRoom)
def change_user_count_post(instance, using, **kwargs):
    instance.room.connections_number = CahUsersInRoom.objects.filter(room=instance.room).count()
    instance.room.is_full = instance.room.full()
    if instance.room.connections_number == 0:
        instance.room.game_state = ROOM_GAME_STATE_WAITING_PLAYERS
    instance.room.save()


@receiver(models.signals.post_save, sender=CahUsersInRoom)
def change_user_count(instance, using, **kwargs):
    print(str(instance), " action:", instance.action_required, "old:", instance.prev_action_required)
    if instance.action_required != instance.prev_action_required:
        instance.prev_action_required = instance.action_required
        instance.save()
        if instance.room.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
            num_awaiting = CahUsersInRoom.objects.filter(room=instance.room, action_required=True).count()
            if num_awaiting == 0:
                instance.room.game_state = ROOM_GAME_STATE_VOTING
                instance.room.save()
        elif instance.room.game_state == ROOM_GAME_STATE_VOTING:
            num_awaiting = CahUsersInRoom.objects.filter(room=instance.room, action_required=True).count()
            if num_awaiting == 0:
                instance.room.game_state = ROOM_GAME_STATE_OTHER_PICK_CARD
                instance.room.save()


@receiver(models.signals.post_save, sender=CahRoom)
def on_game_state_update(instance, created, raw, **kwargs):
    if instance.game_state != instance.prev_game_state:
        if instance.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
            print("models ROOM_GAME_STATE_HOST_PICKS_CARD")
            answer_cards = list(CahCardGame.objects.filter(room=instance, card__card_type=CARD_TYPE_ANSWER,
                                                        card_state=CARD_STATE_WAITING))
            random.shuffle(answer_cards)
            users_in_room = CahUsersInRoom.objects.filter(room=instance)
            users_num = users_in_room.count()
            if instance.prev_game_state == ROOM_GAME_STATE_WAITING_PLAYERS:
                print("new game")
                users_in_room[0].set_host()
                for i, user in enumerate(users_in_room):
                    for card in answer_cards[i:users_num*10:users_num]:
                        CahCardGame.objects.filter(id=card.id).update(user=user, card_state=CARD_STATE_IN_GAME)
            else:
                print("next round")
                old_host = CahUsersInRoom.objects.get(room=instance, is_host=True)
                #TODO: update score count
                #user.score += 1
                #user.round_score += 1
                #user.save()
                old_host.set_next_host()
                for i, user in enumerate(users_in_room):
                    for card in answer_cards[i:users_num:users_num]: #TODO: add 2 cards of question card required 2 cards
                        CahCardGame.objects.filter(id=card.id).update(user=user, card_state=CARD_STATE_IN_GAME)
                CahCardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE_PREV).update(card_state=CARD_STATE_PLAYED)
                CahCardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE).update(card_state=CARD_STATE_VOTE_PREV)
            print("models ROOM_GAME_STATE_OTHER_PICK_CARD")
            CahUsersInRoom.objects.filter(room=instance, is_host=False).update(action_required=True, prev_action_required=True)
        elif instance.game_state == ROOM_GAME_STATE_VOTING:
            print("models ROOM_GAME_STATE_VOTING")
            CahUsersInRoom.objects.filter(room=instance, is_host=False).update(action_required=True, prev_action_required=True)
            print("voting set actions true")
        elif instance.game_state == ROOM_GAME_STATE_WAITING_PLAYERS:
            CahCardGame.objects.filter(room=instance).update(card_state=CARD_STATE_WAITING, user=None)
            CahUsersInRoom.objects.filter(room=instance).update(is_host=False, score=0, action_required=False)
            CahCardVotes.objects.filter(room=instance).delete()
        instance.prev_game_state = instance.game_state
        instance.save()
        async_to_sync(get_channel_layer().group_send)(
            "chat_" + str(instance.id),
            {
                'type': 'game_state_changed',
                'game_state': instance.game_state,
            }
        )
