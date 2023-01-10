from django.urls import path
from . import views


urlpatterns = [
    path('register/',views.CompanyRegisterAPIView.as_view()),
    path('dashboard/',views.CompanyDashboardAPIView.as_view()),
    path('programs/',views.CompanyProgramAPIView.as_view()),
    path('program/detail/<int:pk>',views.CompanyProgramDetailsAPIView.as_view()),
    path('program/<int:pk>',views.CompanyDeleteProgramAPIView.as_view()),
    path('submission/',views.CompanySubmissionAPIView.as_view()),
    path('submission/detail/<int:pk>',views.CompanySubmissionDetailsAPIView.as_view()),
    path('submission/reject/<int:pk>',views.CompanySubmissionRejectAPIView.as_view()),
    path('submission/accept/<int:pk>',views.CompanySubmissionAcceptAPIView.as_view()),
    path('leaderboard/',views.CompanyLeaderBoardAPIView.as_view()),
    path('setting/',views.CompanySettingsAPIView.as_view()),
    path('leaderboard/detail/<int:pk>',views.CompanyLeaderBoardDetailAPIView.as_view()),
    path('setting/changename/',views.CompanySettingsChangeNameAPIView.as_view()),
    path('setting/changeusername/',views.CompanySettingschangeUserNameAPIView.as_view()),
    path('setting/changepassword/',views.CompanySettingsUpdatePasswordAPIView.as_view()),
    path('setting/changeimage/',views.CompanySettingsUploadImageAPIView.as_view()),
    

    

]
