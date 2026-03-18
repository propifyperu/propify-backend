from django.urls import path

from apps.users.views import MeView, TokenObtainView, TokenRefreshAPIView

urlpatterns = [
    path("token/", TokenObtainView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
