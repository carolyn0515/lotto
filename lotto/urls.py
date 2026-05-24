from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
app_name = "lotto"
urlpatterns=[
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/",
         auth_views.LoginView.as_view(template_name="lotto/login.html"),
         name="login",),
    path("logout/",
         auth_views.LogoutView.as_view(template_name="lotto/home"),
         name="logout"),
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
    path("manager/draws/create/", views.create_draw_view, name="create_draw"),
    path("manager/draws/<int:draw_id>/run/", views.run_draw_view, name="run_draw"),
    path("manager/sales/", views.admin_sales_report, name="admin_sales_report"),
    path("watch-ad/", views.watch_ad, name="watch_ad"),
    path(
    "draws/<int:draw_id>/purchase/ml/",
    views.purchase_ml,
    name="purchase_ml",
),
]