from django.urls import path
from . import views

urlpatterns = [
    path("login/",views.LoginAPIView.as_view()),
    path('email_verification/<str:token>/',views.ConfirmEmailAPIView.as_view()),
    path('optional_email_verification/<str:token>/',views.OptionalEmailAPIView.as_view()),
    path("validatephone/",views.PhoneValidateAPIView.as_view()),
    path("forgotpassword/",views.ForgotPasswordAPIView.as_view()),
    path('changepassword/',views.ChangePasswordAPIView.as_view()),
    path('verify_email/',views.EmailVerificationAPIView.as_view()),
    path("logout/",views.Logout.as_view()),
]
