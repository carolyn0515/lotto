from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ManualPurchaseForm
from .models import Draw,Ticket
from .services import purchase_ticket

def home(request):
    current_draw = (
        Draw.objects
        .filter(is_drawn=False)
        .order_by("round_number")
        .first()
    )
    context = {
        "current_draw": current_draw,
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
def my_tickets(request):
    tickets = (
        Ticket.objects
        .filter(user=request.user)
        .select_related("draw")
        .order_by("-created_at")
    )