# core/throttles.py
from rest_framework.throttling import AnonRateThrottle


class ConnexionRateThrottle(AnonRateThrottle):
    scope = "connexion"