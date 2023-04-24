from django.urls import path
from . import views


urlpatterns = [
    path('register/',views.ProfessionalRegisterAPIView.as_view()),
    path('dashboard/',views.ProfessionalDashboardAPIView.as_view()),
    path('programs/',views.ProfessionalProgramAPIView.as_view()),
    path('program/details/<int:pk>',views.ProfessionalProgramDetailsAPIView.as_view()),
    path('submission/',views.ProfessionalSubmissionAPIView.as_view()),
    path('submission/details/<int:pk>',views.ProfessionalSubmissionDetailsAPIView.as_view()),
    path('leaderboard/',views.ProfessionalLearderAPIView.as_view()),
    path('leaderboard/details/<int:pk>',views.ProfessionalLeaderDetailsAPIView.as_view()),
    path('setting/',views.ProfessionalSettingsAPIView.as_view()),
    path('settings/changename/',views.ProfessionalSettingsNameDescriptionAPIView.as_view()),
    path('settings/changeusername/',views.ProfessionalSettingsUserEmailAPIView.as_view()),
    path('settings/changepassword/',views.ProfessionalSettingsUpdatePasswordAPIView.as_view()),
    path('settings/skill/',views.ProfessionalSettingsSkillsAPIView.as_view()),
    path('settings/skill/<int:pk>',views.ProfessionalDeleteSkillAPIView.as_view()),
    path('settings/uploadimage/',views.ProfessionalSettingsUploadPictureAPIView.as_view()),
    path('settings/resume/',views.ProfessionalSettingsUploadResumeAPIView.as_view()),
    # path('settings/optionalemail/',views.ProfessionalSettingsOptionalEmailAPIView.as_view()),
    path('favourite/',views.ProfessionalFavouriteListAPIView.as_view()),
    path('favourite/<int:pk>',views.PrefessionalFavouritePorgramAPIView.as_view()),
    path('information/',views.ProfessionalInformationAPIView.as_view()),
    path('withdraw/',views.ProfessionalPaymentAPIView.as_view()),

]
