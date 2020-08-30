from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
from datetime import datetime

# Create your models here.

ROOM_GAME_STATE_WAITING_PLAYERS = 0
ROOM_GAME_STATE_HOST_PICKS_CARD = 1
ROOM_GAME_STATE_OTHER_PICK_CARD = 2
ROOM_GAME_STATE_VOTING = 3


class Room(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField('date started', auto_now_add=True)
    connections_number = models.IntegerField(default=0)
    game_state = models.IntegerField(default=0, null=False)
    prev_game_state = models.IntegerField(default=0, editable=False, null=False)
    num_people_action_needed = models.IntegerField(default=0, null=False)
    is_full = models.BooleanField(default=False, null=False)
    story = models.CharField(max_length=255, default="")
    prev_story = models.CharField(max_length=255, default="")
    max_players = models.IntegerField(default=7, null=False)
    games_count = models.IntegerField(default=0, null=False)
    winner_score = models.IntegerField(default=-1, null=False)

    def __init__(self, *args, **kwargs):
        super(Room, self).__init__(*args, **kwargs)
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
        action_required = self.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD
        user_in_room = UsersInRoom.objects.create(user=user, room=self, action_required=action_required)
        # Give user 6 cards
        if self.game_state != ROOM_GAME_STATE_WAITING_PLAYERS:
            cards = list(CardGame.objects.filter(room=self, card_state=CARD_STATE_WAITING))
            random.shuffle(cards)
            for card in cards[:6]:
                CardGame.objects.filter(id=card.id).update(user=user_in_room, card_state=CARD_STATE_IN_GAME)
        self.connections_number = UsersInRoom.objects.filter(room=self).count()
        self.is_full = self.full()
        self.save()
        # async_to_sync(get_channel_layer().group_send)(
        #    "chat_" + str(self.id),
        #    {
        #        'type': 'connections_changed',
        #        'current_number': self.connections_number
        #    }
        # )
        return user_in_room

    def start_game(self):
        CardGame.objects.filter(room=self).update(card_state=CARD_STATE_WAITING, hosts_card=False, user=None)
        UsersInRoom.objects.filter(room=self).update(is_host=False, score=0, round_score=0, action_required=False)
        CardVotes.objects.filter(room=self).delete()

        self.prev_story = ""
        self.game_state = ROOM_GAME_STATE_HOST_PICKS_CARD
        self.games_count += 1
        self.save()

    def stop_game(self):
        self.game_state = ROOM_GAME_STATE_WAITING_PLAYERS
        self.winner_score = UsersInRoom.objects.filter(room=self).aggregate(models.Max("score"))['score__max']
        self.save()

    def full(self):
        return self.connections_number >= self.max_players

    def is_waiting(self):
        return self.game_state == ROOM_GAME_STATE_WAITING_PLAYERS

    def get_winners(self):
        return [str(user.user) for user in UsersInRoom.objects.filter(room=self, score=self.winner_score)]


class GameCardStats(models.Model):
    room_id = models.IntegerField(null=False)
    game_id = models.IntegerField(null=False)
    card_id = models.IntegerField(null=False)
    card_set = models.IntegerField(null=False)
    is_host = models.BooleanField(null=False, default=False)
    story = models.CharField(max_length=255, default="")
    num_votes = models.IntegerField(null=False, default=0)
    num_players = models.IntegerField(null=False)
    max_score = models.IntegerField(null=False)
    points = models.IntegerField(null=False, default=0)
    datetime = models.DateTimeField(null=False)


class UsersInRoom(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
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

    def set_host(self, action_required=True):
        UsersInRoom.objects.filter(room=self.room).update(is_host=False)
        self.is_host = True
        self.action_required = action_required
        self.save()

    def set_next_host(self, next_host_action_required=True):
        if self.is_host:
            next_hosts = UsersInRoom.objects.filter(room=self.room, id__gt=self.id).order_by("id")
            if len(next_hosts) == 0:  # set first user in room to be host
                next_hosts = UsersInRoom.objects.filter(room=self.room).order_by("id")
                if len(next_hosts) == 0:  # set first user in room to be host
                    return
            next_hosts[0].set_host(next_host_action_required)


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

    class Meta:
        unique_together = ["set", "name"]

    def __str__(self):
        return "card" + self.name

    def path(self):
        return self.set.name + "/card" + self.name + ".png"


CARD_STATE_WAITING = 0
CARD_STATE_IN_GAME = 1
CARD_STATE_PLAYED = 2
CARD_STATE_VOTE = 3
CARD_STATE_VOTE_PREV = 4


# Current state of each card in one game
class CardGame(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    card_set = models.ForeignKey(CardSet, on_delete=models.CASCADE)
    card_state = models.IntegerField(default=0, null=False)  # 0 - waiting, 1 - in use
    user = models.ForeignKey(UsersInRoom, null=True, on_delete=models.SET_NULL)
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


class CardVotes(models.Model):
    user = models.ForeignKey(UsersInRoom, on_delete=models.CASCADE)
    card = models.ForeignKey(CardGame, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)


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
            Card.objects.create(set=instance, name=str(i + 1))


@receiver(models.signals.pre_delete, sender=RoomCardSet)
def remove_cards_from_game(instance, using, **kwargs):
    CardGame.objects.filter(card_set=instance.set, room=instance.room).delete()


@receiver(models.signals.pre_delete, sender=UsersInRoom)
def change_user_count_pre(instance, using, **kwargs):
    CardGame.objects.filter(room=instance.room, user=instance, card_state=CARD_STATE_IN_GAME).update(
        card_state=CARD_STATE_WAITING, user=None)
    CardGame.objects.filter(room=instance.room, user=instance, card_state=CARD_STATE_VOTE).update(
        card_state=CARD_STATE_PLAYED, user=None)
    if instance.is_host:
        if instance.room.game_state == ROOM_GAME_STATE_HOST_PICKS_CARD:
            instance.set_next_host(True)
        else:
            instance.set_next_host(False)


@receiver(models.signals.post_delete, sender=UsersInRoom)
def change_user_count_post(instance, using, **kwargs):
    instance.room.connections_number = UsersInRoom.objects.filter(room=instance.room).count()
    instance.room.is_full = instance.room.full()
    if instance.room.connections_number == 0:
        instance.room.game_state = ROOM_GAME_STATE_WAITING_PLAYERS
    if instance.room.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
        num_awaiting = UsersInRoom.objects.filter(room=instance.room, action_required=True).count()
        if num_awaiting == 0:
            instance.room.game_state = ROOM_GAME_STATE_VOTING
            instance.room.save()
    elif instance.room.game_state == ROOM_GAME_STATE_VOTING:
        num_awaiting = UsersInRoom.objects.filter(room=instance.room, action_required=True).count()
        if num_awaiting == 0:
            instance.room.game_state = ROOM_GAME_STATE_HOST_PICKS_CARD
            instance.room.save()
    instance.room.save()
    async_to_sync(get_channel_layer().group_send)(
        "chat_" + str(instance.room.id),
        {
            'type': 'game_state_changed',
            'game_state': instance.room.game_state,
        }
    )
    # async_to_sync(get_channel_layer().group_send)(
    #    "chat_" + str(instance.room.id),
    #    {
    #        'type': 'connections_changed',
    #        'current_number': instance.room.connections_number
    #    }
    # )


@receiver(models.signals.post_save, sender=UsersInRoom)
def change_user_count(instance, using, **kwargs):
    if instance.action_required != instance.prev_action_required:
        instance.prev_action_required = instance.action_required
        instance.save()
        if instance.room.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
            num_awaiting = UsersInRoom.objects.filter(room=instance.room, action_required=True).count()
            if num_awaiting == 0:
                instance.room.game_state = ROOM_GAME_STATE_VOTING
                instance.room.save()
        elif instance.room.game_state == ROOM_GAME_STATE_VOTING:
            num_awaiting = UsersInRoom.objects.filter(room=instance.room, action_required=True).count()
            if num_awaiting == 0:
                if CardGame.objects.filter(room=instance.room, card_state=CARD_STATE_WAITING).count() < UsersInRoom.objects.filter(room=instance.room).count():
                    return instance.room.stop_game()
                instance.room.game_state = ROOM_GAME_STATE_HOST_PICKS_CARD
                instance.room.save()


@receiver(models.signals.post_save, sender=Room)
def on_game_state_update(instance, created, raw, **kwargs):
    if instance.game_state != instance.prev_game_state:
        if instance.game_state == ROOM_GAME_STATE_HOST_PICKS_CARD:
            instance.prev_story = instance.story
            cards = list(CardGame.objects.filter(room=instance, card_state=CARD_STATE_WAITING))
            random.shuffle(cards)
            users_in_room = UsersInRoom.objects.filter(room=instance)
            users_num = users_in_room.count()
            if instance.prev_game_state == ROOM_GAME_STATE_WAITING_PLAYERS:
                users_in_room[0].set_host()
                for i, user in enumerate(users_in_room):
                    for card in cards[i:users_num * 6:users_num]:
                        CardGame.objects.filter(id=card.id).update(user=user, card_state=CARD_STATE_IN_GAME)
                CardVotes.objects.filter(room=instance).delete()
            else:
                old_host = UsersInRoom.objects.get(room=instance, is_host=True)
                host_card = CardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE, user=old_host)[0]
                host_votes = CardVotes.objects.filter(room=instance, card=host_card)
                users = UsersInRoom.objects.filter(room=instance)
                num_players = users.count()
                stat_time = datetime.now()
                max_points = num_players + 1  # (users.count() - 2)*1 + 3
                if host_votes.count() == num_players - 1:  # all but host get +3
                    for user in users:
                        if user.id != old_host.id:
                            user.round_score = 3
                            user.score += 3
                            user.save()
                        else:
                            old_host.round_score = 0
                            old_host.save()
                    for card in CardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE):
                        num_votes = 0
                        if card.hosts_card:
                            num_votes = host_votes.count()
                        card_stat = GameCardStats(room_id=instance.id,
                                                  game_id=instance.games_count,
                                                  card_id=card.card.id,
                                                  card_set=card.card_set.id,
                                                  is_host=card.hosts_card,
                                                  story=instance.prev_story,
                                                  num_votes=num_votes,
                                                  num_players=num_players,
                                                  max_score=max_points,
                                                  points=card.user.round_score,
                                                  datetime=stat_time)
                        card_stat.save()
                else:
                    users.update(round_score=0)
                    if host_votes.count() > 0:
                        old_host.score += 3
                        old_host.round_score = 3
                        old_host.save()
                    for vote in host_votes:
                        vote.user.score += 3
                        vote.user.round_score += 3
                        vote.user.save()
                    for vote in CardVotes.objects.filter(room=instance, card__card_state=CARD_STATE_VOTE):
                        vote.card.user.score += 1
                        vote.card.user.round_score += 1
                        vote.card.user.save()
                    for card in CardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE):
                        num_votes = CardVotes.objects.filter(room=instance, card=card).count()
                        card_stat = GameCardStats(room_id=instance.id,
                                                  game_id=instance.games_count,
                                                  card_id=card.card.id,
                                                  card_set=card.card_set.id,
                                                  is_host=card.hosts_card,
                                                  story=instance.prev_story,
                                                  num_votes=num_votes,
                                                  num_players=num_players,
                                                  max_score=max_points,
                                                  points=card.user.round_score,
                                                  datetime=stat_time)
                        card_stat.save()
                old_host.set_next_host()
                for i, user in enumerate(users_in_room):
                    for card in cards[i:users_num:users_num]:
                        CardGame.objects.filter(id=card.id).update(user=user, card_state=CARD_STATE_IN_GAME)
                CardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE_PREV).update(
                    card_state=CARD_STATE_PLAYED)
                CardGame.objects.filter(room=instance, card_state=CARD_STATE_VOTE).update(
                    card_state=CARD_STATE_VOTE_PREV)
        elif instance.game_state == ROOM_GAME_STATE_OTHER_PICK_CARD:
            UsersInRoom.objects.filter(room=instance, is_host=False).update(action_required=True,
                                                                            prev_action_required=True)
        elif instance.game_state == ROOM_GAME_STATE_VOTING:
            UsersInRoom.objects.filter(room=instance, is_host=False).update(action_required=True,
                                                                            prev_action_required=True)
        instance.prev_game_state = instance.game_state
        instance.save()
        async_to_sync(get_channel_layer().group_send)(
            "chat_" + str(instance.id),
            {
                'type': 'game_state_changed',
                'game_state': instance.game_state,
            }
        )
