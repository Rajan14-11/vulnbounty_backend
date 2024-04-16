from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CompanyRegisterSerializer, CompanyProgramSerializer, CompanySubmissionSerializer, CompanyProfessionalLeaderBoardSerializer, CompanyStudentLeaderBoardSerializer, ComapnyImageUploadSerializer, CompanySettingsSerializer, CompanyLoginDetailsSerializer, CompanyExtendedUserSerializer, CompanyCreateProgramSerializer, ScopeEntrySerializer
from .serializers import CompanyChangeNameSerializer, DropdownMenuOptionSerializer, ResumeUploadSerializer, CreateSubmissionSerializer, ProgramCollectionSerializer, CompanyProgramSerializer, CompanyChangeUserNameSerializer, CompanyUpdatePasswordSerializer, CompanyWalletHistory,CompanySerializer
from .models import company, DropdownMenuOption, companyProgram, ProgramCollection, submission, payments, company_login_details, company_wallet, company_wallet_history, ScopeEntry
from django.contrib.auth.models import User
from datetime import date
from django.db import connection
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from StudentApi.models import Student
from ProfessionalApi.models import professional
from rest_framework.decorators import api_view, permission_classes
import re
from twilio.rest import Client
from .helpers import send_email_verification_mail, send_optional_email_verification_mail
from MainApi.helpers import error_handle
import uuid
import stripe
from django.conf import settings
import os
from django.contrib.auth import authenticate, login, logout
from MainApi.models import ExtendUser, ValidateNumber, messages
from django.contrib.auth.hashers import make_password
import requests
import json
from rest_framework import status, generics
from .renderers import UserRender
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from MainApi.serializers import PhoneValidation
from .decorators import allowed_users
from ProfessionalApi.models import private_invitation
from django.shortcuts import redirect, render
from rest_framework import generics, status
from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import Count
from django.utils import timezone
import stripe
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.decorators import login_required
# from .forms import CompanyPaymentForm

stripe.api_key = settings.STRIPE_SECRET_KEY
# Geneerate Token Manually


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def send_email_verification_mail(request, recipient_email, email_token):
    subject = 'Email Verification'
    message = f'Click the following link to verify your email: {request.build_absolute_uri("/api/email_verification")}/{email_token}/'
    from_email = 'rajangouyal740@gmail.com'
    recipient_list = [recipient_email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False


class CompanyRegisterAPIView(APIView):
    renderer_classes = [UserRender]

    def post(self, request, format=None):
        serializer = CompanyRegisterSerializer(data=request.data)
        if serializer.is_valid():
            email_token = str(uuid.uuid4())
            user = serializer.save()
            company_obj = company.objects.create(
                company_user=user, email_verification_token=email_token, terms_and_policy=True)
            token = get_tokens_for_user(user)
            if company_obj:
                company_wallet.objects.create(company=company_obj)
                print(request, email_token)
                email_sent = send_email_verification_mail(
                    request, user.email, email_token)
                if email_sent:
                    message = 'Account created Successfully! Verify your email'
                else:
                    message = 'Email sending failed. Please retry.'
            else:
                message = 'Account not created retry again'
            return Response({"message": message})

        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)


class CompanyDashboardAPIView(APIView):

    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]
    # @allowed_users()

    def get(self, request):
        print(request.user.id)
        # try:
        company_obj = company.objects.get(company_user=request.user.id)
        submission_today = submission.objects.filter(
            program__company=request.user.id, created_at__date=date.today()).count()
        submission_this_month = submission.objects.filter(
            program__company=request.user.id, created_at__month=date.today().month).count()
        top_hunter = professional.objects.filter(
            reward__gte=1).order_by("-reward")[:5]
        payment_today = payments.objects.filter(
            transfer_from=company_obj.id, created_at__date=date.today()).aggregate(Sum('amount'))
        payment_this_month = payments.objects.filter(
            transfer_from=company_obj.id, created_at__month=date.today().month).aggregate(Sum('amount'))
        message = "success"
        response = {
            "message": message,
            "data": {
                "submission_today": submission_today,
                "submission_this_month": submission_this_month,
                "top_hunter": CompanyProfessionalLeaderBoardSerializer(top_hunter, many=True).data,
                "payment_today": payment_today,
                "payment_this_month": payment_this_month
            }

        }
        return Response(response)
        # except Exception as e:

        #     message="failed"
        #     response={
        #         "message":message,
        #         "data":None
        #     }
        #     return Response(response)


# class CompanyProgramAPIView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = User.objects.get(id=request.user.id)
#         program_obj = companyProgram.objects.filter(company=user)
#         response = {
#             "message": "success",
#             "data": {
#                 "programs": CompanyProgramSerializer(program_obj, many=True).data
#             }
#         }
#         return Response(response)

#     def post(self, request):
#         # try:
#         #     client_key=request.data('g-recaptcha-response')
#         #     secret_key=settings.RECAPTCHA_SECRET_KEY
#         #     captcha_data={
#         #         "secret":secret_key,
#         #         "response":client_key
#         #     }
#         #     response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
#         #     response=json.loads(response_data.text)
#         #     verify=response['success']
#         # except:
#         #     message="Something went wrong , Retry later"
#         #     return Response({"message":message})
#         verify = True
#         if verify == True:
#             serializer = CompanyCreateProgramSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.validated_data['company'] = request.user
#                 program_obj = serializer.save()
#                 # program_obj.company=request.user
#                 # program_obj.save()
#                 message = "Program created successfully"
#             else:
#                 message = f"Something went wrong: {serializer.errors}"
#             # if serializer.is_valid(raise_exception=True):
#             #     slug=request.data['slug']
#             #     title=request.data['title']
#             #     introduction=request.data['introduction']
#             #     vulnerability_concerns= request.data['vulnerability_concerns']
#             #     target=request.data['target']
#             #     scope_type=request.data['scope_type']
#             #     out_scope_target=request.data['out_target']
#             #     visibility=request.data['visibility']
#             #     p1_min=int(request.data['p1_min'])
#             #     p1_max=int(request.data['p1_max'])
#             #     p2_min=int(request.data['p2_min'])
#             #     p2_max=int(request.data['p2_max'])
#             #     p3_min=int(request.data['p3_min'])
#             #     p3_max=int(request.data['p3_max'])
#             #     p4_min=int(request.data['p4_min'])
#             #     p4_max=int(request.data['p4_max'])
#             #     p5_min=int(request.data['p5_min'])
#             #     p5_max=int(request.data['p5_max'])
#             #     print("slug",slug,"title",title,"introduction",introduction,"vulnerability_concerns",vulnerability_concerns,"target",target,"scope_type",scope_type,"out_scope_target",out_scope_target)
#             #     try:
#             #         max_reward=request.data['max_reward']
#             #     except:
#             #         max_reward=None
#             #         pass
#             #     if not max_reward:
#             #         if not p1_min>0 or not p1_max>0 or not p2_min>0 or not p2_max>0 or not p3_min>0 or not p3_max>0 or not p4_min>0 or not p4_max>0 or not p5_min>0 or not p5_max >0:
#             #             return Response({"message":"Rewards should be positive"})
#             #         reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max]
#             #     else:
#             #         if not p1_min > 0 or not p1_max > 0 or not p2_min > 0 or not p2_max > 0 or not p3_min > 0 or not p3_max > 0 or not p4_min > 0 or not p4_max > 0 or not p5_min > 0 or not p5_max > 0 or not int(max_reward) > 0:
#             #             return Response({"message":"Rewards should be positive"})
#             #         reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max,int(max_reward)]
#             #     reward_list_copy=reward_list[:]
#             #     reward_list_copy.sort()
#             #     if reward_list != reward_list_copy:
#             #         return Response({"message":'The reward should be in increasing order'})

#             # else:
#             #     message='Something went wrong creating program'
#         else:
#             message = error_handle(serializer.errors)
#             print("message", message)
#             return Response(message)
#             # print(title,slug,introduction,vulnerability_concerns,target,scope_type,out_scope_target,visibility,p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max)
#         response = {
#             "message": message,

#         }
#         return Response(response)

class CompanyProgramAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        program_obj = companyProgram.objects.filter(company=user)
        response = {
            "message": "success",
            "data": {
                "programs": CompanyProgramSerializer(program_obj, many=True).data
            }
        }
        return Response(response)

    def post(self, request):
        verify = True
        if verify == True:

            serializer = CompanyCreateProgramSerializer(data=request.data)
            if serializer.is_valid():
                # Extract and save the company profile image if provided
                compan = company.objects.get(company_user=request.user.id)
                profile_image = compan.profile_picture
                if profile_image:
                    serializer.validated_data['profile_image'] = profile_image

                program_obj = serializer.save(company=request.user)
                message = "Program created successfully"
            else:
                message = "Something went wrong, Retry later"
        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)

        response = {
            "message": message,
        }
        return Response(response)

class CompanyProgramDetailsAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = User.objects.get(id=request.user.id)
        if companyProgram.objects.filter(company=user).exists():
            program_obj = companyProgram.objects.get(company=user, id=pk)
            program_serializer = CompanyProgramSerializer(program_obj)
            data = {
                "program": program_serializer.data
            }
            response = {
                "data": data
            }
        else:
            response = {
                "message": "Program does not exits"
            }

        return Response(response)


class CompanyProgramDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, program_id):
        try:
            program = companyProgram.objects.get(id=program_id)
            print(program)
            if program.company == request.user:
                program.delete()
                message = "Program deleted successfully."
                return Response({"message": message})
            else:
                message = "You don't have permission to delete this program."
                return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
        except companyProgram.DoesNotExist:
            message = "Program not found."
            return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)


class CompanySubmissionAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        all_submission = submission.objects.filter(
            program_id__company=request.user)
        user_field_mapping = {}

        for sub in all_submission:
            user_id = sub.user.id
            profe_user = professional.objects.get(
                professional_user=sub.user.id)
    # Add the user ID and the additional field value to the dictionary
    # Here, 'your_field_value' is the value you want to assign to each user
            user_field_mapping[user_id] = profe_user.profile_picture

# Now you can access the additional field value for each user
        for sub in all_submission:
            user_id = sub.user.id
            additional_field_value = user_field_mapping.get(user_id)

        for sub in all_submission:
            profe_user = professional.objects.get(
                professional_user=sub.user.id)
            print(profe_user.profile_picture)
        # pending_submission=submission.objects.filter(program_id__company=request.user,status='pending')
        # accepted_submission=submission.objects.filter(program_id__company=request.user,status='accepted')
        # rejected_submission=submission.objects.filter(program_id__company=request.user,status='rejected')
        # completed_submission=submission.objects.filter(program_id__company=request.user,status='completed')

        data = {
            "all_submission": CompanySubmissionSerializer(all_submission, many=True).data,
            # "pending_submission":CompanySubmissionSerializer(pending_submission,many=True).data,
            # "accepted_submission":CompanySubmissionSerializer(accepted_submission,many=True).data,
            # "rejected_submission":CompanySubmissionSerializer(rejected_submission,many=True).data,
            # "completed_submission":CompanySubmissionSerializer(completed_submission,many=True).data,
        }
        response = {
            "message": "success",
            "data": data
        }
        return Response(response)


class CompanySubmissionDetailsAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            submission_obj = submission.objects.get(
                program__company=request.user.id, id=pk)
            response = {
                "message": "success",
                "data": {
                    "submission_obj": CompanySubmissionSerializer(submission_obj).data
                }
            }
        except Exception as e:
            print(e)
            response = {
                "message": "could not find submission"
            }
        return Response(response)


class CompanySubmissionRejectAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if submission.objects.filter(program__company=request.user.id, id=pk).exists():
            submission.objects.filter(
                program__company=request.user.id, id=pk).update(status="rejected")
            response = {
                "message": "Submission Rejected"
            }
        else:
            response = {
                "message": "Could not find submission"
            }

        return Response(response)


class CompanySubmissionAcceptAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not submission.objects.filter(program__company=request.user, id=pk).exists():
            response = {
                "message": "Could not find submission"
            }
            return Response(response)

        data = submission.objects.get(program__company=request.user, id=pk)
        submission_id = pk
        sender_id = request.user.id
        receiver_id = data.user.id
        message = "Your submission accepted"
        try:
            submission.objects.filter(
                program__company=request.user.id, id=pk).update(status="accepted")
            message_data = messages.objects.create(
                submission_id=submission_id, sender_id=sender_id, receiver_id=receiver_id, text=message)
            response = {
                "message": "Submission Accepeted",
            }
        except:
            response = {
                "message": "Could not find submission"
            }
        return Response(response)


def calculateStreakforUser(user):
    streak = 0
    today = datetime.now()
    start_of_year = today.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_year = today.replace(
        month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
    submissions = submission.objects.filter(
        user=user.professional_user, created_at__gte=start_of_year, created_at__lte=end_of_year).order_by('created_at')

    # Calculate streak
    streaks = defaultdict(int)
    current_month = None
    current_streak = 0

    for sub in submissions.order_by('created_at'):
        submission_month = sub.created_at.month

        if current_month != submission_month:
            current_month = submission_month
            current_streak = 0

        current_streak += 1
        streaks[submission_month] = max(
            streaks[submission_month], current_streak)

    return streaks


def calculate_streak_points(streak):
    if streak >= 3:
        return 5
    elif streak >= 6:
        return 10
    elif streak >= 9:
        return 15
    elif streak >= 12:
        return 50
    else:
        return 0


def calculate_points():
    submissions = submission.objects.filter(status='accepted').values(
        'user').annotate(total_points=Count('id'))
    streak_points = {}

    points = {}
    for sub in submissions:
        user_id = sub['user']
        profe_user = professional.objects.get(
            professional_user=user_id)
        streaks = calculateStreakforUser(profe_user)
        streak = 0
        for month, value in streaks.items():

            if value == 0:
                streak = 0
            else:
                streak += 1

        streak_points[user_id] = streak
        streak = streak_points.get(user_id, 0)
        points[user_id] = sub['total_points'] * \
            10 + calculate_streak_points(streak)
    return points


class CompanyLeaderBoardAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    # def get(self, request):
    #     data = professional.objects.filter(reward__gte=1).order_by('-reward')
    #     data1 = Student.objects.filter(reward__gte=1).order_by('-reward')

    #     response = {
    #         "data": {
    #             "professional_obj": CompanyProfessionalLeaderBoardSerializer(data, many=True).data,
    #             "student_obj": CompanyStudentLeaderBoardSerializer(data1, many=True).data
    #         }

    #     }

    def get(self, request):
        try:

            total_points = calculate_points()
            sorted_rankings = sorted(
                total_points.items(), key=lambda x: x[1], reverse=True)
            message = "Success"
        except:
            serializer = None
            message = "Failed"

        leaderboard_data = []
        for user_id, total_points in sorted_rankings:
            try:
                professional_data = professional.objects.get(
                    professional_user=user_id)
                serializer = CompanyProfessionalLeaderBoardSerializer(professional_data)
                leaderboard_data.append({
                    'user_id': user_id,
                    'total_points': total_points,
                    'professional': serializer.data
                })
            except professional.DoesNotExist:
                pass

        response = {
            "message": message,
            'data': leaderboard_data
        }

        return Response(response)


class CompanyLeaderBoardDetailAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if Student.objects.filter(student_user__id=pk).exists():
            data = Student.objects.get(student_user__id=pk)
            message = "success"
            serializer = CompanyStudentLeaderBoardSerializer(data).data
        elif professional.objects.filter(professional_user__id=pk).exists():
            data = professional.objects.get(professional_user__id=pk)
            message = "success"
            serializer = CompanyProfessionalLeaderBoardSerializer(data).data
        else:
            message = "failed"
            serializer = None

        response = {
            "message": message,
            "data": {
                "leaderdata": serializer
            }
        }
        return Response(response)


class CompanySettingsAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            program_count = submission.objects.filter(
                program__company=request.user.id).count()
            company_obj = company.objects.get(company_user=request.user.id)
            total_payment = payments.objects.filter(
                transfer_from=company_obj.id).aggregate(Sum('amount'))
            company_login_details_obj = company_login_details.objects.get(
                company=company_obj)
            try:
                ExtendUser_obj = ExtendUser.objects.get(user=request.user.id)
                validate_obj = ValidateNumber

            except:
                ExtendUser.objects.create(user=request.user)
                ExtendUser_obj = ExtendUser.objects.get(user=request.user.id)

            try:
                ValidateNumber_obj = ValidateNumber.objects.get(
                    user=ExtendUser_obj.id)
                if ValidateNumber_obj.status == True:
                    ValidateNumber_status = "True"
                else:
                    ValidateNumber_status = "False"
            except:
                ValidateNumber_obj = None
                ValidateNumber_status = "False"

            response = {
                "message": "success",
                "data": {
                    "details": CompanySettingsSerializer(company_obj).data,
                    "program_count": program_count,
                    "total_payment": total_payment,
                    "login_details": CompanyLoginDetailsSerializer(company_login_details_obj).data,
                    "ExtendUser": CompanyExtendedUserSerializer(ExtendUser_obj).data,
                    "ValidateNumber": PhoneValidation(ValidateNumber_obj).data,
                }

            }
        except Exception as e:
            response = {
                "message": "failed",
                "data": None
            }
            print(e,'settings')
        return Response(response)


class CompanySettingsChangeNameAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CompanyChangeNameSerializer(data=request.data)
        if serializer.is_valid():
            try:
                first_name = request.data['first_name']
                last_name = request.data['last_name']
                profile_description = request.data['description']
                if not first_name.isalpha() or not last_name.isalpha():
                    message = "first name or last name is invalid , only alphabet"
                    return Response({"message": message})
                User.objects.filter(id=request.user.id).update(
                    first_name=first_name, last_name=last_name)
                company.objects.filter(company_user=request.user).update(
                    description=profile_description)
                message = 'Successfully updated !'
            except Exception as e:
                message = "Failed"
                print(e)
        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)

        response = {
            "message": message
        }
        return Response(response)


class CompanySettingschangeUserNameAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CompanyChangeUserNameSerializer(data=request.data)
        message = []
        if serializer.is_valid():
            # try:
            regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
            print("reached_up")
            username = request.data['username']
            email = request.data['email']
            password = request.data['password']
            if not username or not email or not password:
                message = "Fields should not be empty"
            else:
                if not re.search(regex, username):
                    message = "Allowed are alphabet,number and apostrophe"
                else:
                    pass

            user = authenticate(
                request, username=request.user.username, password=password)
            if user is not None:
                print("no user")
                if request.user.username != username:

                    if User.objects.filter(username=username).exists():
                        message.append('Username already taken')

                    else:
                        User.objects.filter(id=user.id).update(
                            username=username)
                        message.append(' Username successfully updated !')
                if user.email != email and not ExtendUser.objects.filter(optional_email=email, user=user).exists():

                    if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
                        print("reached in email2")
                        message.append('Email already taken')
                    else:
                        token = str(uuid.uuid4())

                        try:
                            ExtendUser_obj = ExtendUser.objects.get(
                                user=user.id)
                            if user.email != email != ExtendUser_obj.optional_email:
                                print("update")
                                ExtendUser.objects.filter(user=request.user.id).update(
                                    optional_email=email, optional_email_token=token, optional_email_status=False)
                                send_optional_email_verification_mail(
                                    email, token)
                                message.append(
                                    'Email successfully updated, Now Verify the email')

                            else:
                                message.append('You already added this Email')

                        except:
                            print("create")
                            ExtendUser.objects.create(
                                user=user, optional_email=email, optional_email_token=token)
                            send_email_verification_mail(request, email, token)
                            message.append(
                                'Email successfully Added, Now Verify the email')

            else:
                message = error_handle(serializer.errors)
                print("message", message)
                return Response(message)

            # except Exception as e:
            #     message="failed"
            # print(e)``
            response = {
                "message": message,
                "data": None
            }

        else:
            response = {
                "message": "something went wrong",
                "data": None
            }

        return Response(response)


class CompanySettingsUpdatePasswordAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = CompanyUpdatePasswordSerializer(data=request.data)
        if serializer.is_valid():
            password_1 = request.data['password1']
            password_2 = request.data['password2']
            password_3 = request.data['password3']
            if not password_1 or not password_2 or not password_3:
                message = "Fields should not be empty"
            user_obj = authenticate(
                request, username=request.user.username, password=password_1)
            if user_obj is not None:
                if not password_2 and not password_3:
                    message = "New password confirm password should not be empty and length more than 9"
                if password_2 == password_3:
                    print("reached")
                    password = make_password(password_2)
                    User.objects.filter(id=request.user.id).update(
                        password=password)
                    user_obj = authenticate(
                        username=request.user.username, password=password)
                    login(request, user_obj)
                    message = "New password updated successfully"
                else:
                    message = "New password and confirm password not match"
            else:
                message = "Old password not match"

            print('if')
        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)

        response = {
            "data": None,
            "message": message
        }
        return Response(response)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "No user found with this email address"}, status=status.HTTP_400_BAD_REQUEST)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        current_site = get_current_site(request)
        # Create a URL in your URLs configuration for password reset confirmation
        reset_url = reverse('password-reset-confirm')

        reset_link = f"http://{current_site.domain}{reset_url}?uid={uid}&token={token}"

        send_mail(
            subject="Password Reset",
            message=f"Click the following link to reset your password: {reset_link}",
            from_email="your@email.com",
            recipient_list=[email],
        )

        return Response({"detail": "Password reset email sent"}, status=status.HTTP_200_OK)


class CompanySettingsUploadImageAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        data = company.objects.get(company_user=request.user.id)
        serializer = ComapnyImageUploadSerializer(
            data, data=request.data, partial=True)
        if serializer.is_valid():
            if data.profile_picture == 'Null':
                serializer.save()
                message = "Profile picture successfully updated !"
                print("if")
            else:
                print("else")
                file_exists = os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
                serializer.save()
                message = "Profile picture successfully updated !"

        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)
        response = {
            "message": message
        }
        return Response(response)


class CompanyWalletHistoryApIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        company_obj = company.objects.get(company_user=request.user.id)
        wallet_obj = company_wallet_history.objects.filter(company=company_obj)
        response = {
            "data": {
                "companyWallet": CompanyWalletHistory(wallet_obj, many=True).data
            }
        }
        return Response(response)


class CompanyPrivateInvitationAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk1, pk2, format=None):
        try:
            # if private_invitation.objects.filter()
            # pk1-> hunter id
            # pk2 -> program id
            program = companyProgram.objects.get(company=request.user, id=pk2)
            hunter = professional.objects.get(professional_user=pk1)
            private_invitation.objects.create(program=program, hunter=hunter)
            response = {
                "message": "success",
            }
        except:
            response = {
                "message": "failed"

            }
        return Response(response)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def UpdateCompanyProgram(request, program_id):
    try:
        program = companyProgram.objects.get(pk=program_id)
    except companyProgram.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Check if the user has permission to update this program
    if request.user != program.company:
        return Response({"error": "You do not have permission to update this program."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = CompanyProgramSerializer(program, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteProgramAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, program_id):
        try:
            program = companyProgram.objects.get(id=program_id)

            # Check if the program belongs to the current user or implement permission checks as needed.
            if program.company == request.user:
                program.delete()
                message = "Program deleted successfully."
                return Response({"message": message})
            else:
                message = "You don't have permission to delete this program."
                return Response({"message": message}, status=status.HTTP_403_FORBIDDEN)
        except companyProgram.DoesNotExist:
            message = "Program not found."
            return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)


class CreateProgramCollection(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProgramCollectionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ListUserCollections(request):
    collections = ProgramCollection.objects.filter(user=request.user)
    serializer = ProgramCollectionSerializer(collections, many=True)
    return Response(serializer.data)

# Create an API to list the programs within a collection


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ListProgramsInCollection(request, collection_id):
    try:
        collection = ProgramCollection.objects.get(
            pk=collection_id, user=request.user)
    except ProgramCollection.DoesNotExist:
        return Response({"error": "Collection not found."}, status=status.HTTP_404_NOT_FOUND)

    programs = collection.programs.all()
    program_data = [CompanyProgramSerializer(
        program).data for program in programs]

    return Response({"collection_id": collection_id, "programs": program_data})

# API for creating a program


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def StoreProgramDataApi(request):
    data = request.data
    program = companyProgram.objects.create(
        company=request.user,
        slug=data['slug'],
        title=data['title'],
        introduction=data['introduction'],
    )
    program_serializer = CompanyProgramSerializer(program)
    return Response({"message": "Program data stored successfully"}, status=status.HTTP_201_CREATED)

# class StoreProgramAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = CompanyProgramSerializer(data=request.data)

#         if serializer.is_valid():
#             program = serializer.save(company=request.user)
#             message = "Program stored successfully"
#             return Response({"message": message, "program_id": program.id})
#         else:
#             message = "Something went wrong while storing the program."
#             return Response({"message": message}, status=400)


class StoreProgramAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        program_details = request.data
        submission_obj = submission(
            user=request.user,
            program_details=program_details
        )
        submission_obj.save()
        return Response({"message": "Program stored successfully in submission"})


class ResumeUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ResumeUploadSerializer(data=request.data)

        if serializer.is_valid():
            resume = serializer.validated_data['resume']

            # Generate a unique filename for the uploaded file
            unique_filename = str(uuid.uuid4()) + \
                resume.name[resume.name.rfind('.'):]
            file_path = 'resumes/' + unique_filename  # Adjust the file path as needed

            with open(file_path, 'wb+') as destination:
                for chunk in resume.chunks():
                    destination.write(chunk)

            # Return the URL of the uploaded file
            file_url = request.build_absolute_uri(file_path)

            return Response({"detail": "Resume uploaded successfully", "file_url": file_url}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DropdownMenuOptionListView(generics.ListAPIView):
    queryset = DropdownMenuOption.objects.all()
    serializer_class = DropdownMenuOptionSerializer


class DropdownMenuOptionSelectView(generics.CreateAPIView):
    serializer_class = DropdownMenuOptionSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        selected_option = serializer.validated_data
        if selected_option['is_custom']:
            dropdown_menu_option = DropdownMenuOption.objects.create(
                label=selected_option['label'],
                value=selected_option['value'],
            )

            dropdown_menu_option.save()

        return Response(selected_option, status=status.HTTP_201_CREATED)


class ScopeEntryListCreateView(generics.GenericAPIView):
    serializer_class = ScopeEntrySerializer

    def get(self, request, *args, **kwargs):
        program_id = self.kwargs['program_id']
        scope_entries = ScopeEntry.objects.filter(program_id=program_id)
        serializer = self.get_serializer(scope_entries, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        program_id = self.kwargs['program_id']
        program = companyProgram.objects.get(id=program_id)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['program'] = program
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CompanyBankDetailCreateView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         serializer = CompanyBankDetailSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(company=request.user.company)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class CompanyBankDetailRetrieveView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:
#             # Use the correct related name for the reverse relation
#             bank_details = request.user.company.company_bank_details.all()
#             serializer = CompanyBankDetailSerializer(bank_details, many=True)
#             return Response(serializer.data)
#         except company.DoesNotExist:
#             return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
#         except CompanyBankDetail.DoesNotExist:
#             return Response({"error": "Company bank details not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class AddMoneyToCompanyWalletView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         try:
#             amount = float(request.data.get('amount'))
#         except (TypeError, ValueError):
#             return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

#         company_wallet = CompanyWallet.objects.filter(
#             company=request.user.company).first()
#         company_bank_detail = CompanyBankDetail.objects.filter(
#             company=request.user.company).first()

#         if company_wallet and company_bank_detail and amount >= 0:
#             try:
#                 # Check if stripe_charge_id is available
#                 if company_bank_detail.stripe_charge_id:
#                     # Use the existing stripe_charge_id as the source
#                     source = company_bank_detail.stripe_charge_id
#                 else:
#                     # If stripe_charge_id is not available, create a new source (bank account) using the Stripe API
#                     source = stripe.Source.create(
#                         type="ach_credit_transfer",
#                         currency="usd",  # Replace with the appropriate currency code
#                         # Replace with the actual email
#                         owner={"email": request.user.email},
#                     )
#                 try:
#                     source = stripe.Source.retrieve(source)
#                     print("Source Object:", source)
#                 except stripe.error.StripeError as e:
#                     print(f"Stripe error: {e}")

#                     # Save the new stripe_charge_id in company_bank_detail
#                     company_bank_detail.stripe_charge_id = source.id
#                     company_bank_detail.save()

#                 # Create a charge using the Stripe API
#                 stripe_charge_response = stripe.Charge.create(
#                     amount=int(amount * 100),
#                     currency="usd",  # Replace with the appropriate currency code
#                     source=source,
#                     description="Charge for company XYZ",
#                 )
#                 # Extract the Stripe transaction ID
#                 stripe_transaction_id = stripe_charge_response.id
#             except stripe.error.StripeError as e:
#                 return Response({"error": f"Stripe error: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#             # Update the serializer with the new balance and Stripe transaction ID
#             company_wallet_serializer = CompanyWalletSerializer(
#                 company_wallet,
#                 data={'balance': company_wallet.balance + amount,
#                       'stripe_transaction_id': stripe_transaction_id}
#             )

#             if company_wallet_serializer.is_valid():
#                 company_wallet_serializer.save()
#                 return Response({"message": "Money added to the company's wallet, and bank details updated successfully"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Company wallet update failed"}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"error": "Company wallet or bank details not found or invalid amount"}, status=status.HTTP_400_BAD_REQUEST)


# class WithdrawMoneyFromCompanyWalletView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         try:
#             amount = float(request.data.get('amount'))
#         except (TypeError, ValueError):
#             return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

#         company_wallet = CompanyWallet.objects.filter(
#             company=request.user.company).first()
#         company_bank_detail = CompanyBankDetail.objects.filter(
#             company=request.user.company).first()

#         if company_wallet and company_bank_detail and company_wallet.balance >= amount >= 0:
#             # Add withdrawn money to the company's bank account using Stripe
#             try:
#                 stripe.Transfer.create(
#                     amount=int(amount * 100),  # Amount in cents
#                     currency="inr",
#                     # Replace with the actual Stripe transaction ID
#                     source_transaction=company_wallet.stripe_transaction_id,
#                     # Replace with the actual Stripe account ID
#                     destination=company_bank_detail.stripe_account_id,
#                 )
#             except stripe.error.StripeError as e:
#                 return Response({"error": f"Stripe error: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#             # Update the serializer with the new balance
#             company_wallet_serializer = CompanyWalletSerializer(
#                 company_wallet, data={'balance': company_wallet.balance - amount})
#             if company_wallet_serializer.is_valid():
#                 company_wallet_serializer.save()
#                 return Response({"message": "Money withdrawn from company's wallet and bank details updated successfully"}, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Company wallet update failed"}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"error": "Company wallet or bank details not found or invalid amount"}, status=status.HTTP_400_BAD_REQUEST)


# class TransferMoneyToProfessionalView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         try:
#             amount = float(request.data.get('amount'))
#         except (TypeError, ValueError):
#             return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

#         company_wallet = request.user.company.wallet.first()
#         professional = request.user.professional

#         if company_wallet and professional and amount >= 0:
#             try:
#                 stripe.Transfer.create(
#                     amount=int(amount * 100),  # Amount in cents
#                     currency="inr",
#                     # Replace with the actual Stripe transaction ID
#                     source_transaction=company_wallet.stripe_transaction_id,
#                     # Replace with the actual Stripe account ID
#                     destination=professional.wallet.stripe_account_id,
#                 )
#             except stripe.error.StripeError as e:
#                 return Response({"error": f"Stripe error: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#             return Response({"message": "Money transferred to professional's wallet successfully"}, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "Company wallet, professional, or invalid amount"}, status=status.HTTP_400_BAD_REQUEST)


# class CompanyWalletDetailsView(APIView):
#     renderer_classes = [UserRender]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         company_wallet = CompanyWallet.objects.filter(
#             company=request.user.company).first()

#         if company_wallet:
#             serializer = CompanyWalletSerializer(company_wallet)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "Company wallet not found"}, status=status.HTTP_404_NOT_FOUND)

# # @login_required


# class PaymentAPIView(generics.CreateAPIView):
#     serializer_class = CompanyPaymentSerializer

#     def create(self, request, *args, **kwargs):
#         form = CompanyPaymentForm(request.data)

#         if request.method == "POST":
#             username = request.POST.get('username')  # Assuming username is provided in the form data
#             amount = request.POST.get('amount')

#         # Retrieve the User instance corresponding to the provided username
#             try:
#                 user_instance = User.objects.get(username=username)
#             except User.DoesNotExist:
#             # Handle the case where the user with the specified username does not exist
#                 return Response("User not found", status=400)  # or handle it based on your requirements

#         # Create Payment instance without using a form
#             payment = Transaction(user=user_instance, amount=amount)

#         # Set the user using request.user if available
#             if request.user.is_authenticated:
#                 payment.user = request.user

#         # Save the payment instance
#             payment.save()

#         # Create a Stripe PaymentIntent
#             stripe.api_key = settings.STRIPE_SECRET_KEY
#             intent = stripe.PaymentIntent.create(
#             amount=int(payment.amount * 100),
#             currency='usd',
#             metadata={'payment_id': "payment.id"}
#             )

#             return Response({'client_secret': intent.client_secret}, status=status.HTTP_201_CREATED)

#         return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)


# class ProcessPaymentAPIView(generics.CreateAPIView):
#     def create(self, request, *args, **kwargs):
#         client_secret = request.data.get('client_secret')

#         if client_secret:
#             stripe.api_key = settings.STRIPE_SECRET_KEY
#             intent = stripe.PaymentIntent.confirm(client_secret)

#             if intent.status == 'succeeded':
#                 # Update the Payment model
#                 payment_id = intent.metadata['payment_id']
#                 payment = Transaction.objects.get(id=payment_id)
#                 payment.paid = True
#                 payment.save()

#                 return Response({'message': 'Payment successful!'}, status=status.HTTP_200_OK)

#         return Response({'error': 'Invalid client_secret provided.'}, status=status.HTTP_400_BAD_REQUEST)
