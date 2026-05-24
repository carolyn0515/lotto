from django.urls import path
from . import views
app_name = "lotto"
urlpatterns=[
    path("", views.home, name="home"),
    path(
        "draws/<int:draw_id>/purchase/manual/",
        views.purchase_manual,
        name="purchase_manual",
    ),
    path("my_tickets/", views.my_tickets, name="my_tickets"),
]