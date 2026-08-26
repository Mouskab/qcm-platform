# abonnements/urls_web.py
from django.urls import path
from .views_web import (
    PlansWebView, SouscrireWebView, SouscrireCashWebView,
    PacksWebView, AcheterPackView, AcheterPackCashWebView,
)

urlpatterns = [
    path("", PlansWebView.as_view(), name="plans-web"),
    path("<int:plan_id>/souscrire/", SouscrireWebView.as_view(), name="souscrire-web"),
    path("<int:plan_id>/souscrire-cash/", SouscrireCashWebView.as_view(), name="souscrire-cash-web"),

    path("packs/", PacksWebView.as_view(), name="packs-web"),
    path("packs/<int:pack_id>/acheter/", AcheterPackView.as_view(), name="acheter-pack-web"),
    path("packs/<int:pack_id>/acheter-cash/", AcheterPackCashWebView.as_view(), name="acheter-pack-cash-web"),
]