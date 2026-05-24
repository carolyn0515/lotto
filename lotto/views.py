from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import login
from .forms import DrawCreateForm, ManualPurchaseForm, SignUpForm
from .models import Draw, Ticket, WinningResult, UserProfile
from .services import (
    create_next_draw,
    generate_random_numbers,
    purchase_ticket,
    reward_ad_coin,
    run_draw,
)
from .ml_service import recommend_lotto_numbers

def home(request):
    current_draw = (
        Draw.objects
        .filter(is_drawn=False)
        .order_by("round_number")
        .first()
    )

    latest_drawn = (
        Draw.objects
        .filter(is_drawn=True)
        .order_by("-round_number")
        .first()
    )

    context = {
        "current_draw": current_draw,
        "latest_drawn": latest_drawn,
    }

    return render(request, "lotto/home.html", context)

@login_required
def purchase_manual(request, draw_id):
    draw = get_object_or_404(Draw, id=draw_id)
    if request.method == "POST":
        form = ManualPurchaseForm(request.POST)
        if form.is_valid():
            numbers = form.get_numbers()
            try:
                purchase_ticket(
                    user=request.user,
                    draw=draw,
                    numbers=numbers,
                    purchase_type=Ticket.PURCHASE_TYPE_MANUAL
                )
                messages.success(request, "수동 번호 구매가 완료되었습니다.")
                return redirect("lotto:my_tickets")
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = ManualPurchaseForm()

    context = {
        "draw": draw,
        "form": form,
    }

    return render(request, "lotto/purchase_manual.html", context)

@login_required
def purchase_auto(request, draw_id):
    draw = get_object_or_404(Draw, id=draw_id)
    try:
        numbers = generate_random_numbers()
        purchase_ticket(
            user=request.user,
            draw=draw,
            numbers=numbers,
            purchase_type=Ticket.PURCHASE_TYPE_AUTO,
        )
        messages.success(request, f"자동 번호 구매가 완료되었습니다. 번호: {numbers}")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("lotto:my_tickets")

@login_required
def my_tickets(request):
    tickets = (
        Ticket.objects
        .filter(user=request.user)
        .select_related("draw", "winning_result")
        .order_by("-created_at")
    )

    context = {
        "tickets": tickets,
    }

    return render(request, "lotto/my_tickets.html", context)

@staff_member_required
def admin_draw_list(request):
    draws = Draw.objects.order_by("-round_number")

    context = {
        "draws": draws,
    }

    return render(request, "lotto/admin_draw_list.html", context)

@staff_member_required
def run_draw_view(request, draw_id):
    draw = get_object_or_404(Draw, id=draw_id)
    if request.method == "POST":
        try:
            run_draw(draw)
            messages.success(
                request,
                f"{draw.round_number}"
            )
        except ValueError as e:
            messages.error(request, str(e))
    return redirect("lotto:admin_draw_list")

@staff_member_required
def admin_sales_report(request):
    draws = Draw.objects.order_by("-round_number")
    reports = []

    for draw in draws:
        tickets = Ticket.objects.filter(draw=draw)
        results = WinningResult.objects.filter(ticket__draw=draw)

        total_ticket_count = tickets.count()
        manual_ticket_count = tickets.filter(
            purchase_type=Ticket.PURCHASE_TYPE_MANUAL
        ).count()
        auto_ticket_count = tickets.filter(
            purchase_type=Ticket.PURCHASE_TYPE_AUTO
        ).count()
        ml_ticket_count = tickets.filter(
            purchase_type=Ticket.PURCHASE_TYPE_ML
        ).count()

        reports.append({
            "draw": draw,
            "total_ticket_count": total_ticket_count,
            "manual_ticket_count": manual_ticket_count,
            "auto_ticket_count": auto_ticket_count,
            "result_count": results.count(),
            "ml_ticket_count": ml_ticket_count,
            "first_rank_count": results.filter(rank="1등").count(),
            "second_rank_count": results.filter(rank="2등").count(),
            "third_rank_count": results.filter(rank="3등").count(),
            "fourth_rank_count": results.filter(rank="4등").count(),
            "fifth_rank_count": results.filter(rank="5등").count(),
            "losing_count": results.filter(rank="낙첨").count(),
        })

    context = {
        "reports": reports,
    }

    return render(request, "lotto/admin_sales_report.html", context)

@staff_member_required
def create_draw_view(request):
    if request.method == "POST":
        form = DrawCreateForm(request.POST)

        if form.is_valid():
            close_at = form.cleaned_data["close_at"]

            draw = create_next_draw(close_at)

            messages.success(
                request,
                f"{draw.round_number}회차가 생성되었습니다."
            )

            return redirect("lotto:admin_draw_list")
    else:
        form = DrawCreateForm()

    context = {
        "form": form,
    }

    return render(request, "lotto/create_draw.html", context)

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            UserProfile.objects.get_or_create(
                user=user,
                coin=10
            )
            login(request, user)
            messages.success(request, "회원가입이 완료되었습니다.")
            return redirect("lotto:home")
    else:
        form = SignUpForm()
    
    context = {
        "form": form,
    }

    return render(request, "lotto/signup.html", context)

@login_required
def watch_ad(request):
    if request.method == "POST":
        new_coin = reward_ad_coin(request.user)
        messages.success(
            request,
            f"광고 시청 보상으로 코인 5개가 지급되었습니다. 현재 보유 코인: {new_coin}개"
        )
        return redirect("lotto:home")
    return render(request, "lotto/watch_ad.html")

@login_required
def purchase_ml(request, draw_id):
    draw = get_object_or_404(Draw, id=draw_id)

    if request.method != "POST":
        messages.error(request, "잘못된 요청입니다.")
        return redirect("lotto:home")
    
    try:
        numbers = recommend_lotto_numbers(
            user=request.user,
            draw=draw,
        )

        purchase_ticket(
            user=request.user,
            draw=draw,
            numbers=numbers,
            purchase_type=Ticket.PURCHASE_TYPE_ML,
        )

        messages.success(request, f"ML 추천 번호 구매가 완료되었습니다. 번호: {numbers}")

    except ValueError as e:
        messages.error(request, str(e))

    return redirect("lotto:my_tickets")
