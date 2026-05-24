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
    path(
        "draws/<int:draw_id>/purchase/auto/",
        views.purchase_auto,
        name="purchase_auto",
    ),
    path("my_tickets/", views.my_tickets, name="my_tickets"),
    path("manager/draws/", views.admin_draw_list, name="admin_draw_list"),
    path("manager/draws/<int:draw_id>/run/", views.run_draw_view, name="run_draw"),
]