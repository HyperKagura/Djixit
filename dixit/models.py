from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver

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


class CardSet(models.Model):
    name = models.CharField(max_length=200)

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

    def __str__(self):
        return "card_" + str(self.id)


CARD_STATE_WAITING = 0
CARD_STATE_IN_GAME = 1
CARD_STATE_PLAYED = 2


class CardGame(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    room_card_set = models.ForeignKey(RoomCardSet, on_delete=models.CASCADE)
    card_state = models.IntegerField(default=0)  # 0 - waiting, 1 - in use
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ["card", "room_card_set"]

    def __str__(self):
        return str(self.room_card_set) + " " + str(self.card)

    def set_user(self, user_id):
        self.card_state = CARD_STATE_IN_GAME
        self.user_id = user_id
        self.save()

    def set_state_waiting(self):
        self.card_state = CARD_STATE_WAITING
        self.user_id = None
        self.save()

    def set_state_played(self):
        self.card_state = CARD_STATE_PLAYED
        self.save()


@receiver(models.signals.post_save, sender=RoomCardSet)
def add_cards_to_game(instance, created, raw, **kwargs):
    if created:
        cards = Card.objects.filter(set=instance.set)
        for card in cards:
            CardGame.objects.create(card=card, room_card_set=instance, card_state=CARD_STATE_WAITING)
