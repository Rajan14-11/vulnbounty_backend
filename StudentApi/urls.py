from django.urls import path
from .views import *
# from .views import profile_setting
# from . import views 

urlpatterns = [
    path("dashboard/",DashboardView.as_view()),
    path('programs',ProgramView.as_view()),
    path('programs/filter',Programfilter.as_view()),
    path('program_details/',Program_details_view.as_view()),
    path('submission',SubmissionView.as_view()),
    path('student_submission',Student_submission_details_view.as_view()),
    path('submit_program',Submit_program_view.as_view()),
    path('chat',Chat_view.as_view()),
    path('payment',Payment_view.as_view()),
    path('payment_success/<int:amount>',Payment_success_view.as_view()),
    path('leader_board', Leader_board_view.as_view()),
    path('leaderboard_details/<str:id>',Leaderboard_detail_view.as_view()),
    path('settings/profile',Profile_setting.as_view()),
    path('update_password',Update_Password.as_view()),
    path('add_skills',Add_Skills.as_view()),
    path('privacy_settings',Privacy_setting_view.as_view()),
    path('delete_skill/<int:id>',Delete_skills_view.as_view()),
    path('add_img',Update_img.as_view()),
    path('update_resume',Update_resume.as_view()),
    path('update_old_password',Update_Old_Password.as_view()),
    path('email_verification',Email_verification.as_view()),
    path('phone_validation',Phone_validation.as_view()),
    path('logout',Logout_view.as_view()),
    path('student_information/<int:id>',Student_infromation_view.as_view()),
    path('student_favourite_program/<int:id>',Student_favourite_program_view.as_view()),
    path('student_favourite_program_list',Student_favourite_program_list_view.as_view())
]

