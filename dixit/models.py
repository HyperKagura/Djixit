from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver

# Create your models here.

ROOM_CONNECTIONS_LIMIT = 2

ROOM_GAME_STATE_WAITING_PLAYERS = 0
ROOM_GAME_STATE_HOST_PICKS_CARD = 1
ROOM_GAME_STATE_OTHER_PICK_CARD = 2
ROOM_GAME_STATE_VOTING = 3
ROOM_GAME_STATE_ROUND_RESULT = 4


class Room(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('date started')
    connections_number = models.IntegerField(default=0)
    game_state = models.IntegerField(default=0, null=False)
    num_people_action_needed = models.IntegerField(default=0, null=False)
    round_host = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    is_full = models.BooleanField(default=False, null=False)

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

    def add_connection(self, user):
        self.connections_number += 1
        user_in_room = UsersInRoom.objects.create(user=user, room=self)
        self.is_full = self.full()
        self.save()
        return user_in_room

    def full(self):
        return self.connections_number >= ROOM_CONNECTIONS_LIMIT


class UsersInRoom(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)


class CardSet(models.Model):
    name = models.CharField(max_length=200)
    cards_number = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class RoomCardSet(models.Model):
    set = models.ForeignKey(CardSet, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["room_id", "set_id"]

    def __str__(self):
        room_name = self.room.name
        card_set = self.set.name
        return room_name + ": " + card_set


class Card(models.Model):
    set = models.ForeignKey(CardSet, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default="", null=False)

    def __str__(self):
        return "card_" + self.name


CARD_STATE_WAITING = 0
CARD_STATE_IN_GAME = 1
CARD_STATE_PLAYED = 2
CARD_STATE_VOTE = 3


class CardGame(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    card_set = models.ForeignKey(CardSet, on_delete=models.CASCADE)
    card_state = models.IntegerField(default=0)  # 0 - waiting, 1 - in use
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

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


@receiver(models.signals.post_save, sender=RoomCardSet)
def add_cards_to_game(instance, created, raw, **kwargs):
    if created:
        cards = Card.objects.filter(set=instance.set)
        for card in cards:
            CardGame.objects.create(card=card, room=instance.room, card_set=instance.set, card_state=CARD_STATE_WAITING)


@receiver(models.signals.post_save, sender=CardSet)
def create_cards_in_set(instance, created, raw, **kwargs):
    if created:
        for i in range(instance.cards_number):
            Card.objects.create(set=instance, name=str(i+1))


@receiver(models.signals.pre_delete, sender=RoomCardSet)
def remove_cards_from_game(instance, using, **kwargs):
    CardGame.objects.filter(card_set=instance.set, room=instance.room).delete()


@receiver(models.signals.pre_delete, sender=UsersInRoom)
def change_user_count(instance, using, **kwargs):
    instance.room.connections_number -= 1
    instance.room.is_full = instance.room.full()
    instance.room.save()
