from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CompanyRegisterSerializer, CompanyProgramSerializer, CompanySubmissionSerializer, CompanyProfessionalLeaderBoardSerializer, CompanyStudentLeaderBoardSerializer, ComapnyImageUploadSerializer, CompanySettingsSerializer, CompanyLoginDetailsSerializer, CompanyExtendedUserSerializer, CompanyCreateProgramSerializer, CompanyCreateProgramSaveSerializer
from .serializers import CompanyChangeNameSerializer, CompanyChangeUserNameSerializer, CompanyUpdatePasswordSerializer, CompanyWalletHistory
from .models import company, companyProgram, submission, payments, company_login_details, company_wallet, company_wallet_history
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Sum
from StudentApi.models import Student
from ProfessionalApi.models import professional
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
from rest_framework import status
from .renderers import UserRender
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from MainApi.serializers import PhoneValidation
from .decorators import allowed_users
# Geneerate Token Manually


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


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
                send_email_verification_mail(request, user.email, email_token)
                message = 'Account created Successfully ! verify your email'
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
        # try:
        #     client_key=request.data('g-recaptcha-response')
        #     secret_key=settings.RECAPTCHA_SECRET_KEY
        #     captcha_data={
        #         "secret":secret_key,
        #         "response":client_key
        #     }
        #     response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
        #     response=json.loads(response_data.text)
        #     verify=response['success']
        # except:
        #     message="Something went wrong , Retry later"
        #     return Response({"message":message})
        verify = True
        if verify == True:
            serializer = CompanyCreateProgramSerializer(data=request.data)
            if serializer.is_valid():
                program_obj = serializer.save(company=request.user)
                # program_obj.company=request.user
                # program_obj.save()
                message = "Program created successfully"
            else:
                message = "Something went wrong , Retry later"
            # if serializer.is_valid(raise_exception=True):
            #     slug=request.data['slug']
            #     title=request.data['title']
            #     introduction=request.data['introduction']
            #     vulnerability_concerns= request.data['vulnerability_concerns']
            #     target=request.data['target']
            #     scope_type=request.data['scope_type']
            #     out_scope_target=request.data['out_target']
            #     visibility=request.data['visibility']
            #     p1_min=int(request.data['p1_min'])
            #     p1_max=int(request.data['p1_max'])
            #     p2_min=int(request.data['p2_min'])
            #     p2_max=int(request.data['p2_max'])
            #     p3_min=int(request.data['p3_min'])
            #     p3_max=int(request.data['p3_max'])
            #     p4_min=int(request.data['p4_min'])
            #     p4_max=int(request.data['p4_max'])
            #     p5_min=int(request.data['p5_min'])
            #     p5_max=int(request.data['p5_max'])
            #     print("slug",slug,"title",title,"introduction",introduction,"vulnerability_concerns",vulnerability_concerns,"target",target,"scope_type",scope_type,"out_scope_target",out_scope_target)
            #     try:
            #         max_reward=request.data['max_reward']
            #     except:
            #         max_reward=None
            #         pass
            #     if not max_reward:
            #         if not p1_min>0 or not p1_max>0 or not p2_min>0 or not p2_max>0 or not p3_min>0 or not p3_max>0 or not p4_min>0 or not p4_max>0 or not p5_min>0 or not p5_max >0:
            #             return Response({"message":"Rewards should be positive"})
            #         reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max]
            #     else:
            #         if not p1_min > 0 or not p1_max > 0 or not p2_min > 0 or not p2_max > 0 or not p3_min > 0 or not p3_max > 0 or not p4_min > 0 or not p4_max > 0 or not p5_min > 0 or not p5_max > 0 or not int(max_reward) > 0:
            #             return Response({"message":"Rewards should be positive"})
            #         reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max,int(max_reward)]
            #     reward_list_copy=reward_list[:]
            #     reward_list_copy.sort()
            #     if reward_list != reward_list_copy:
            #         return Response({"message":'The reward should be in increasing order'})

            # else:
            #     message='Something went wrong creating program'
        else:
            message = error_handle(serializer.errors)
            print("message", message)
            return Response(message)
            # print(title,slug,introduction,vulnerability_concerns,target,scope_type,out_scope_target,visibility,p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max)
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


class CompanyDeleteProgramAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        print(pk)
        try:
            companyProgram.objects.get(company=request.user, id=pk).delete()
            response = {
                "message": "Deleted Successfully"
            }

        except Exception as e:
            print(e)
            response = {
                "message": "Program Not found"
            }

        return Response(response)


class CompanySubmissionAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        all_submission = submission.objects.filter(
            program_id__company=request.user)
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


class CompanyLeaderBoardAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = professional.objects.filter(reward__gte=1).order_by('-reward')
        data1 = Student.objects.filter(reward__gte=1).order_by('-reward')

        response = {
            "data": {
                "professional_obj": CompanyProfessionalLeaderBoardSerializer(data, many=True).data,
                "student_obj": CompanyStudentLeaderBoardSerializer(data1, many=True).data
            }

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
            print(e)
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
            print(e)
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
