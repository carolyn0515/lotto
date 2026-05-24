import random

from django.utils import timezone

from .models import Draw, Ticket, WinningResult

def validate_lotto_numbers(numbers):
    if len(numbers) != 6:
        raise ValueError("로또 번호는 정확히 6개여야 합니다.")

    if len(set(numbers)) != 6:
        raise ValueError("로또 번호는 중복될 수 없습니다.")

    for number in numbers:
        if not isinstance(number, int):
            raise ValueError("로또 번호는 정수여야 합니다.")

        if number < 1 or number > 45:
            raise ValueError("로또 번호는 1 이상 45 이하이어야 합니다.")


def validate_purchase_type(purchase_type):
    valid_types = [
        Ticket.PURCHASE_TYPE_AUTO,
        Ticket.PURCHASE_TYPE_MANUAL,
    ]

    if purchase_type not in valid_types:
        raise ValueError("올바르지 않은 구매 방식입니다.")


def validate_draw_is_open(draw):
    if draw.is_drawn:
        raise ValueError("이미 추첨이 완료된 회차에는 티켓을 구매할 수 없습니다.")

    if timezone.now() >= draw.close_at:
        raise ValueError("판매가 마감된 회차에는 티켓을 구매할 수 없습니다.")

# user
def purchase_ticket(user, draw, numbers, purchase_type):
    validate_lotto_numbers(numbers)
    validate_purchase_type(purchase_type)
    validate_draw_is_open(draw)
    validate_user_has_enough_coin(user)

    ticket = Ticket.objects.create(
        user=user,
        draw=draw,
        numbers=numbers,
        purchase_type=purchase_type,
    )

    decrease_user_coin(user)
    
    return ticket

TICKET_PRICE = 1

def validate_user_has_enough_coin(user):
        if user.profile.coin < TICKET_PRICE:
            raise ValueError("코인이 부족하여 티켓을 구매할 수 없습니다.")
        
def decrease_user_coin(user):
    user.profile.coin -= TICKET_PRICE
    user.profile.save()


def calculate_rank(ticket_numbers, winning_numbers, bonus_number):
    matched_count = len(set(ticket_numbers) & set(winning_numbers))
    matched_bonus = bonus_number in ticket_numbers

    if matched_count == 6:
        rank = "1등"
    elif matched_count == 5 and matched_bonus:
        rank = "2등"
    elif matched_count == 5:
        rank = "3등"
    elif matched_count == 4:
        rank = "4등"
    elif matched_count == 3:
        rank = "5등"
    else:
        rank = "낙첨"

    return matched_count, matched_bonus, rank

# user_result
def create_winning_results(draw):
    tickets = Ticket.objects.filter(draw=draw)

    for ticket in tickets:
        matched_count, matched_bonus, rank = calculate_rank(
            ticket.numbers,
            draw.winning_numbers,
            draw.bonus_number
        )
        WinningResult.objects.create(
            ticket=ticket,
            matched_count=matched_count,
            matched_bonus=matched_bonus,
            rank=rank
        )

def validate_draw_can_be_run(draw):
    if draw.is_drawn:
        raise ValueError("이미 추첨이 완료된 회차입니다.")

    if timezone.now() < draw.close_at:
        raise ValueError("아직 판매 마감 전이므로 추첨할 수 없습니다.")

# 관리자
def run_draw(draw):
    validate_draw_can_be_run(draw)

    winning_numbers = sorted(random.sample(range(1, 46), 6))

    bonus_candidates = list(set(range(1, 46)) - set(winning_numbers))
    bonus_number = random.choice(bonus_candidates)

    draw.winning_numbers = winning_numbers
    draw.bonus_number = bonus_number
    draw.is_drawn = True
    draw.drawn_at = timezone.now()
    draw.save()

    create_winning_results(draw)

    return draw

def generate_random_numbers():
    return sorted(random.sample(range(1, 46), 6))

def create_next_draw(close_at):
    last_draw = Draw.objects.order_by("-round_number").first()
    if last_draw is None:
        next_round_number = 1
    else:
        next_round_number = last_draw.round_number + 1
    draw = Draw.objects.create(
        round_number = next_round_number,
        close_at = close_at,
    )
    return draw
