from django.conf import settings
from django.db import models

class Draw(models.Model):
    round_number = models.PositiveIntegerField(unique=True)
    winning_numbers = models.JSONField(null=True, blank=True)
    bonus_number = models.PositiveIntegerField(null=True, blank=True)
    is_drawn = models.BooleanField(default=False)
    drawn_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField()

    def __str___(self):
        return f"{self.round_number}회차"

class Ticket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    draw = models.ForeignKey(
        Draw,
        on_delete=models.CASCADE
    )
    PURCHASE_TYPE_AUTO = "AUTO"
    PURCHASE_TYPE_MANUAL = "MANUAL"
    PURCHASE_TYPE_CHOICES = [
        (PURCHASE_TYPE_AUTO, "자동"),
        (PURCHASE_TYPE_MANUAL, "수동"),
    ]
    numbers = models.JSONField()
    purchase_type = models.CharField(
        max_length=10,
        choices=PURCHASE_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.draw.round_number}회차 - {self.numbers}"
    
class WinningResult(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="winning_result"
    )
    matched_count = models.PositiveIntegerField()
    matched_bonus = models.BooleanField(default=False)
    rank = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket} - {self.rank}"