from django.urls import path, re_path

from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import LogoutView, PasswordResetConfirmView
from user.views import CustomPasswordChangeView, CustomPasswordResetView, CustomLoginView, CustomRegisterView, UserView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", CustomRegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("password-reset/", CustomPasswordResetView.as_view(), name="reset"),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path("password-change/", CustomPasswordChangeView.as_view(), name="change"),
    re_path(r"^account-confirm-email/", VerifyEmailView.as_view(), name="account_email_verification_sent"),
    re_path(r"^account-confirm-email/(?P<key>[-:\w]+)/$", VerifyEmailView.as_view(), name="account_confirm_email"),
]
