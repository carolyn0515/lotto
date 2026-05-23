from django.shortcuts import render

from .models import Draw

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