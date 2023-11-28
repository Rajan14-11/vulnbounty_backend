from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from CompanyApi.models import companyProgram,submission
from django.db.models import Q
from CompanyApi.serializers import CompanyProgramSerializer,CompanySubmissionSerializer
from django.contrib.auth.models import User
from .serializers import *
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate, login, logout
import re
import uuid
from MainApi.models import ExtendUser,ValidateNumber
from .helpers import send_email_verification_mail,send_optional_email_verification_mail,error_handle
import os
from twilio.rest import Client
from django.conf import settings
from datetime import date
import requests
import json
from CompanyApi.models import payments
from django.db.models import Sum
from .renderers import UserRender
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from CompanyApi.models import company

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class ProfessionalRegisterAPIView(APIView):
     renderer_classes=[UserRender]
     def post(self,request,format=None):

        serializer=ProfessionalRegisterSdrializer(data=request.data)
        if serializer.is_valid():
            email_token = str(uuid.uuid4())
            user=serializer.save()
            professional_obj = professional.objects.create(professional_user=user,email_verification_token=email_token,terms_and_policy=True)
            token=get_tokens_for_user(user)
            if professional_obj:
                professional_wallet.objects.create(professional=professional_obj)
                send_email_verification_mail(request,user.email,email_token )
                message='Account created Successfully ! verify your email'
            else:
                message='Account not created retry again'
            return Response({"token":token,"message":message})

        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ProfessionalDashboardAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            submission_today=submission.objects.filter(user=request.user.id,created_at__date=date.today()).count()
            submission_this_month=submission.objects.filter(user=request.user.id,created_at__month=date.today().month).count()
            leaderboard= professional.objects.filter(reward__gte=1).order_by('-reward')[:5]
            program=companyProgram.objects.filter(created_at=date.today())[:5]
            payment_today = payments.objects.filter(transfer_to=request.user.id,created_at__date=date.today()).aggregate(Sum('amount'))
            payment_this_month=payments.objects.filter(transfer_to =request.user.id,created_at__month=date.today().month).aggregate(Sum('amount'))

            response={
                "message":'success',
                "data":{'user':request.user.username,
            "submission_today":submission_today,
            "submission_this_month":submission_this_month,
            "top_hunter":ProfessionalDashbordserializer(leaderboard,many=True).data,
            "program":CompanyProgramSerializer(program,many=True).data,
            "payment_today":payment_today,
            "payment_this_month":payment_this_month
            }}
        except Exception as e:
            print(e)
            response={
                "message":"Failed",
                "data":None
            }
        return Response(response)

class QuizAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        questions_data = request.data.get('questions', [])

        user_answers = []

        for question_data in questions_data:
            question_id = question_data.get('question_id')
            user_answer = question_data.get('user_answer')

            try:
                question = QuizQuestion.objects.get(id=question_id)
            except QuizQuestion.DoesNotExist:
                return Response({"message": f"Question with id {question_id} not found"}, status=status.HTTP_404_NOT_FOUND)

            user_answers.append({
                'question': question.id,
                'user_answer': user_answer
            })

            UserAnswer.objects.create(user=request.user, question=question, user_answer=user_answer)

        # Calculate score
        correct_answers = UserAnswer.objects.filter(
            user=request.user,
            question__correct_answer=models.F('user_answer')
        ).count()

        total_questions = len(questions_data)
        score = (correct_answers / total_questions) * 100

        response_data = {
            'message': 'Answers submitted successfully',
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'user_answers': user_answers,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class ProfessionalProgramAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professional_obj = professional.objects.get(professional_user=request.user)
        # professional_information_obj = professional_information.objects.get(professional=professional_obj.id)
        # region = professional_information_obj.country_names

        # Fetch company programs
        data = companyProgram.objects.all().filter((Q(region='all')))

        # Fetch invited programs
        invited_program = private_invitation.objects.filter(hunter=professional_obj.id)

        # Serialize both company programs and invited programs
        company_programs_data = CompanyProgramSerializer(data, many=True).data
        invited_program_data = PrivateInvitationSerializer(invited_program, many=True).data

        # Create the response
        response = {
            "message": "success",
            "data": {
                "programs": company_programs_data,
                "invited_programs": invited_program_data,
            }
        }

        return Response(response)

class CertificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CertificateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            response_data = {
                'message': 'Certificate added successfully',
                'certificate_data': serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListCertificatesAPIView(APIView):
    def get(self, request):
        certificates = Certificate.objects.all()
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DeleteCertificateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, certificate_id):
        try:
            certificate = Certificate.objects.get(pk=certificate_id)
        except Certificate.DoesNotExist:
            return Response({'message': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        certificate.delete()
        return Response({'message': 'Certificate deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class UpdateCertificateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, certificate_id):
        try:
            certificate = Certificate.objects.get(pk=certificate_id)
        except Certificate.DoesNotExist:
            return Response({'message': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CertificateSerializer(certificate, data=request.data)

        if serializer.is_valid():
            serializer.save()
            response_data = {
                'message': 'Certificate updated successfully',
                'certificate_data': serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeactivateAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        user.is_active = False
        user.save()

        response_data = {
            'message': 'Account deactivated successfully',
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class ProfessionalProgramDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        # if submission.objects.filter(program=id,user=request.user.id).exists():
        try:
            data=companyProgram.objects.get(id=pk)
            message="Success"
            serializer=CompanyProgramSerializer(data).data
        except:
            serializer=None
            message="Failed"


        response={
            "message":message,
            "data":{
                "program_obj":serializer
            }
        }
        return Response(response)

class ProfessionalSubmissionAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        all_submission=submission.objects.filter(user=request.user.id)


        response={
            "message":"success",
            "data":{
                "all_submission":CompanySubmissionSerializer(all_submission,many=True).data,
            }
        }

        return Response(response)
    def post(self,request):
        serializer=ProfessionalprogramSubmissionSerializer(data=request.data)
        if  serializer.is_valid():
            program_obj=companyProgram.objects.get(id=serializer.data['program_id'])
            if submission.objects.filter(program=program_obj,user=request.user).exists():
                return Response({"message":"already done"})
            else:
                user = submission.objects.create(
                title=serializer.data['title'],
                report=serializer.data['report'],
                program=program_obj,
                user=request.user)
                message="success"
            return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            return Response(message)


class ResumeUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ResumeUploadSerializer(data=request.data)

        if serializer.is_valid():
            resume = serializer.validated_data['resume']

            unique_filename = str(uuid.uuid4()) + resume.name[resume.name.rfind('.'):]
            file_path = 'resumes/' + unique_filename

            file_content = resume.read()

            ResumeModel.objects.create(file_content=file_content)

            return Response({"detail": "Resume uploaded successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResumeDeleteAPIView(APIView):
    def post(self, request, resume_id, *args, **kwargs):
        try:
            resume = ResumeModel.objects.get(pk=resume_id)
            resume.delete()
            return Response({"detail": "Resume deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ResumeModel.DoesNotExist:
            return Response({"detail": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfessionalSubmissionDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            data=submission.objects.get(program=pk,user=request.user.id)
            response={
            "message":"Success",
            "data":{
                "submission_details_obj":CompanySubmissionSerializer(data).data
            }
            }
        except:
            response={
            "message":"Failed",
            "data":None
        }
        return Response(response)

class ProfessionalLearderAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data = professional.objects.filter(reward__gte=1).order_by('-reward')
            serialzer=ProfessionalDashbordserializer(data,many=True).data
            message="Success"
        except :
            serialzer=None
            message="Failed"

        response={
            "message":message,
            "data":{
                "professional_obj":serialzer
            }
        }

        return Response(response)

class UpdateInvitationPreferenceAPIView(APIView):
    queryset = professional.objects.all()
    serializer_class = ProfessionalSerializer

    def post(self, request, pk=None):
        professional = self.get_object()
        value = request.data.get('value', None)

        if value is not None:
            professional.invitation_preference = value
            professional.save()
            return Response({'message': 'Invitation preference updated successfully.'})
        else:
            return Response({'error': 'Value is required to update invitation preference.'}, status=400)

class FilterProfessionalsByInvitationPreferenceAPIView(APIView):
    queryset = professional.objects.all()
    serializer_class = ProfessionalSerializer

    def get(self, request):
        value = request.query_params.get('value', None)

        if value is not None:
            professionals = professional.objects.filter(invitation_preference=value)
            serializer = ProfessionalSerializer(professionals, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'Value is required to filter by invitation preference.'}, status=400)

class FollowProfessionalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        follower_id = request.data.get('follower_id')
        # print(f"DEBUG: Received follower_id: {follower_id}")
        # print(follower_id)
        try:
           user_to_follow = User.objects.get(id=follower_id)
           professional_to_follow = professional.objects.get(professional_user=user_to_follow)
        #    print(user_to_follow)
        #    print(professional_to_follow)
        except professional.DoesNotExist:
            return Response({"message": "Professional not found"}, status=400)

        # try:

        #     print(user_professional)
        #     print(user_professional.id)
        # except professional.DoesNotExist:
        #     return Response({"message": "User does not have a professional profile"}, status=400)
        user_professional = user.professional_user.get()
        if user_professional.id == professional_to_follow.id:
            return Response({"message": "You cannot follow yourself"}, status=200)

        if Follower.objects.filter(user=user, professional=professional_to_follow).exists():
            return Response({"message": "You are already following this professional"}, status=200)

        Follower.objects.create(user=user, professional=professional_to_follow)

        return Response({"message": "Successfully followed the professional"})

class UnfollowProfessionalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        unfollow_id = request.data.get('unfollow_id')

        try:
           user_to_follow = User.objects.get(id=unfollow_id)
           professional_to_unfollow = professional.objects.get(professional_user=user_to_follow)
        except professional.DoesNotExist:
            return Response({"message": "Professional not found"}, status=404)

        try:
            follower_entry = Follower.objects.get(user=user, professional=professional_to_unfollow)
        except Follower.DoesNotExist:
            return Response({"message": "You are not following this professional"}, status=400)

        follower_entry.delete()

        return Response({"message": "Successfully unfollowed the professional"})

class FollowerProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, follower_id):
        try:
            follower = professional.objects.get(id=follower_id)
            followers = Follower.objects.filter(professional=follower).select_related('user')
            serializer = UserProfileSerializer(follower)
            followers_serializer = UserProfileSerializer(followers, many=True)
            return Response({"user_profile": serializer.data, "followers": followers_serializer.data})
        except professional.DoesNotExist:
            return Response({"message": "Follower not found"}, status=404)

class FollowedUserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, followed_id):
        try:
            followed_user = professional.objects.get(id=followed_id)
            following = Follower.objects.filter(user=followed_user).select_related('professional')
            serializer = UserProfileSerializer(followed_user)
            following_serializer = UserProfileSerializer(following, many=True)
            return Response({"user_profile": serializer.data, "following": following_serializer.data})
        except professional.DoesNotExist:
            return Response({"message": "Followed user not found"}, status=404)

class FollowersListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            professional_user = user.professional_user.get()
        except professional.DoesNotExist:
            return Response({"followers": []})

        # print(Follower.objects.get())
        followers = Follower.objects.filter(professional=professional_user).select_related('professional')
        serializer = FollowerSerializer(followers, many=True)
        return Response({"followers": serializer.data})

class FollowingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        following = Follower.objects.filter(user=user).select_related('professional')
        serializer = FollowerSerializer(following, many=True)  # Use FollowerSerializer here
        return Response({"following": serializer.data})

class SearchUserByUsername(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        try:
            # submissions=submission.objects.filter(program__company=request.user.id)
            # print(submissions)
            profile_instance = professional.objects.get(professional_user=user)
        except professional.DoesNotExist:
            return Response({"message": "User not found in Professional model"}, status=404)

        serializer = UserProfileSerializer(profile_instance)
        return Response(serializer.data)

class GetUpdatedUserProfileAndProfessional(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile_instance = UserProfile.objects.get(user=user)
        professional_instance = professional.objects.get(professional_user=user)

        profile_serializer = UserProfileUpdateSerializer(profile_instance)
        professional_serializer = UpdateProfessionalSerializer(professional_instance)

        profile_data = profile_serializer.data
        professional_data = professional_serializer.data

        return Response({
            "profile": profile_data,
            "professional": professional_data
        })
class RemoveUserFromLeaderboardAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id_to_remove = request.data.get('user_id_to_remove')

        try:
            professional_to_remove = professional.objects.get(id=user_id_to_remove)
            professional_to_remove.delete()
            message = f"User with id {user_id_to_remove} removed from the leaderboard"
        except professional.DoesNotExist:
            message = f"User with id {user_id_to_remove} not found in the leaderboard"
            return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)

        data = professional.objects.filter(reward__gte=1).order_by('-reward')
        serializer = ProfessionalDashbordserializer(data, many=True).data

        response = {
            "message": message,
            "data": {
                "professional_obj": serializer
            }
        }

        return Response(response)

class ProfessionalLeaderDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            data=professional.objects.get(id=pk)
            serialzer=ProfessionalDashbordserializer(data).data
            message="Success"
        except :
            serialzer=None
            message="Failed"
        response={
            "message":message,
            "data":{
                "professional_obj":serialzer
            }
        }
        return Response(response)

class ProfessionalSettingsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            program_count=submission.objects.filter(program__company=request.user.id).count()
            profesional_obj=professional.objects.get(professional_user=request.user.id)
            total_payment=payments.objects.filter(transfer_from = profesional_obj.id).aggregate(Sum('amount'))
            professional_login_details_obj=professional_login_details.objects.get(professional=profesional_obj)
            try:
                ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)

            except:
                ExtendUser.objects.create(user=request.user)
                ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)

            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
                if ValidateNumber_obj.status == True:
                    ValidateNumber_status="True"
                else:
                    ValidateNumber_status="False"
            except:
                ValidateNumber_obj=None
                ValidateNumber_status="False"

            response={
                "message":"success",
                "data":{
                "details":ProfessionalSettingsSerializer( profesional_obj).data,
                "program_count":program_count,
                "total_payment":total_payment,
                "login_details":ProfessionalLoginDetailsSerializer(professional_login_details_obj).data,
                "ExtendUser":ProfessionalExtendedUserSerializer(ExtendUser_obj).data,
                "ValidateNumber":ValidateNumber_obj,}


                }
        except Exception as e:
            response={
                "message":"failed",
                "data":None
            }
            print(e)
        return Response(response)

class ProfessionalSettingsNameDescriptionAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalChangeNameSerialzer(data=request.data)
        if serializer.is_valid():
            try:
                first_name=request.data['first_name']
                last_name=request.data['last_name']
                profile_description=request.data['description']
                if not first_name.isalpha() or not last_name.isalpha():
                    message="first name or last name is invalid , only alphabet"
                    return Response({"message":message})
                User.objects.filter(id=request.user.id).update(first_name=first_name,last_name=last_name)
                professional.objects.filter(professional_user = request.user).update(profile_description=profile_description)
                message='Successfully updated !'
            except Exception as e:
                message="Failed"
                print(e)
            response={
            "message":message
            }
            return Response(response)
        else:
            message=error_handle(serializer.errors)
            return Response(message)



class ProfessionalSettingsUserEmailAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalChangeUserNameSerializer(data=request.data)
        message=[]
        if serializer.is_valid():
            try:
                regex  = "^([a-z]+('[a-z])?[0-9a-z]*)$"
                print("reached_up")
                username = request.data['username']
                email = request.data['email']
                password = request.data['password']
                if not username or not email or not password:
                    message="Fields should not be empty"
                else:
                    if not re.search(regex, username):
                        message="Allowed are alphabet,number and apostrophe"
                    else:
                        pass

                user = authenticate(
                    request, username=request.user.username, password=password)
                if user is not None:
                    if request.user.username != username:

                        if User.objects.filter(username=username).exists():
                            message='Username already taken'

                        else:
                            User.objects.filter(id=user.id).update(username=username)
                            message=' Username successfully updated !'
                    if user.email != email:

                        if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
                            print("reached in email2")
                            message='Email already taken'
                        else:
                            token = str(uuid.uuid4())

                            try:
                                ExtendUser_obj= ExtendUser.objects.get(user=user.id)
                                if user.email != email!=ExtendUser_obj.optional_email:
                                    print("update")
                                    ExtendUser.objects.filter(user=request.user.id).update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                    send_optional_email_verification_mail(email,token)
                                    message='Email successfully updated, Now Verify the email'

                                else:
                                    message='You already added this Email'

                            except:
                                print("create")
                                ExtendUser.objects.create(user=user,optional_email=email,optional_email_token=token)
                                send_email_verification_mail(request,email,token)
                                message='Email successfully Added, Now Verify the email'


                else:
                    message='Password doesnot match'

            except Exception as e:
                message="failed"
                print(e)
            response={
                "message":message,
                "data":None
            }
            return Response(response)

        else:
            message=error_handle(serializer.errors)
            return Response(message)




class ProfessionalSettingsUpdatePasswordAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalUpdatePasswordSerializer(data=request.data)
        if serializer.is_valid():
            password_1=request.data['password1']
            password_2=request.data['password2']
            password_3=request.data['password3']
            if not password_1 or not password_2 or not password_3:
                message="Fields should not be empty"
            user_obj = authenticate(request, username=request.user.username, password=password_1)
            if user_obj is not None:
                if not password_2 and not password_3:
                    message="New password confirm password should not be empty and length more than 9"
                if password_2==password_3:
                    print("reached")
                    password=make_password(password_2)
                    User.objects.filter(id=request.user.id).update(password=password)
                    user_obj =authenticate(username=request.user.username, password=password)
                    login(request,user_obj)
                    message="New password updated successfully"
                else:
                    message="New password and confirm password not match"
            else:
                message="Old password not match"

            print('if')
            response={
            "data":None,
            "message":message
        }
            return Response(response)
        else:
            message=error_handle(serializer.errors)
            return Response(message)





class ProfessionalSettingsSkillsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        try:
            profe_user=professional.objects.get(professional_user=request.user.id)
            professional_obj=professional_skills.objects.filter(user=profe_user.id)
            response={
                "message":"Success",
                "data":{
                    "skills":ProfessionalSkillsSerializer(professional_obj,many=True).data
                }
            }
        except Exception as e:
            response={
                "message":"Failed",
                "data":None
            }
            print(e)
        return Response(response)
    def post(self,request,format=None):
        serializer=ProfessionalSkillsAddSerializer(data=request.data)
        if serializer.is_valid():
            print("reached")
            profe_user=professional.objects.get(professional_user=request.user.id)
            skill=request.data['skill']
            sample_skills = ["A# .NET","A# (Axiom)","A-0 System","A+","A++","ABAP","ABC","ABC ALGOL","ABLE","ABSET","ABSYS","ACC","Accent","Ace DASL","ACL2","ACT-III","Action!","ActionScript","Ada","Adenine","Agda","Agilent VEE","Agora","AIMMS","Alef","ALF","ALGOL 58","ALGOL 60","ALGOL 68","ALGOL W","Alice","Alma-0","AmbientTalk","Amiga E","AMOS","AMPL","APL","App Inventor for Android's visual block language","AppleScript","Arc","ARexx","Argus","AspectJ","Assembly language","ATS","Ateji PX","AutoHotkey","Autocoder","AutoIt","AutoLISP / Visual LISP","Averest","AWK","Axum","B","Babbage","Bash","BASIC","bc","BCPL","BeanShell","Batch (Windows/Dos)","Bertrand","BETA","Bigwig","Bistro","BitC","BLISS","Blue","Bon","Boo","Boomerang","Bourne shell","bash","ksh","BREW","BPEL","C","C--","C++","C#","C/AL","Caché ObjectScript","C Shell","Caml","Candle","Cayenne","CDuce","Cecil","Cel","Cesil","Ceylon","CFEngine","CFML","Cg","Ch","Chapel","CHAIN","Charity","Charm","Chef","CHILL","CHIP-8","chomski","ChucK","CICS","Cilk","CL","Claire","Clarion","Clean","Clipper","CLIST","Clojure","CLU","CMS-2","COBOL","Cobra","CODE","CoffeeScript","Cola","ColdC","ColdFusion","COMAL","Combined Programming Language","COMIT","Common Intermediate Language","Common Lisp","COMPASS","Component Pascal","Constraint Handling Rules","Converge","Cool","Coq","Coral 66","Corn","CorVision","COWSEL","CPL","csh","CSP","Csound","CUDA","Curl","Curry","Cyclone","Cython","D","DASL","DASL","Dart","DataFlex","Datalog","DATATRIEVE","dBase","dc","DCL","Deesel","Delphi","DinkC","DIBOL","Dog","Draco","DRAKON","Dylan","DYNAMO","E","E#","Ease","Easy PL/I","Easy Programming Language","EASYTRIEVE PLUS","ECMAScript","Edinburgh IMP","EGL","Eiffel","ELAN","Elixir","Elm","Emacs Lisp","Emerald","Epigram","EPL","Erlang","es","Escapade","Escher","ESPOL","Esterel","Etoys","Euclid","Euler","Euphoria","EusLisp Robot Programming Language","CMS EXEC","EXEC 2","Executable UML","F","F#","Factor","Falcon","Fancy","Fantom","FAUST","Felix","Ferite","FFP","Fjölnir","FL","Flavors","Flex","FLOW-MATIC","FOCAL","FOCUS","FOIL","FORMAC","@Formula","Forth","Fortran","Fortress","FoxBase","FoxPro","FP","FPr","Franz Lisp","Frege","F-Script","FSProg","G","Google Apps Script","Game Maker Language","GameMonkey Script","GAMS","GAP","G-code","Genie","GDL","Gibiane","GJ","GEORGE","GLSL","GNU E","GM","Go","Go!","GOAL","Gödel","Godiva","GOM (Good Old Mad)","Goo","Gosu","GOTRAN","GPSS","GraphTalk","GRASS","Groovy","Hack (programming language)","HAL/S","Hamilton C shell","Harbour","Hartmann pipelines","Haskell","Haxe","High Level Assembly","HLSL","Hop","Hope","Hugo","Hume","HyperTalk","IBM Basic assembly language","IBM HAScript","IBM Informix-4GL","IBM RPG","ICI","Icon","Id","IDL","Idris","IMP","Inform","Io","Ioke","IPL","IPTSCRAE","ISLISP","ISPF","ISWIM","J","J#","J++","JADE","Jako","JAL","Janus","JASS","Java","JavaScript","JCL","JEAN","Join Java","JOSS","Joule","JOVIAL","Joy","JScript","JScript .NET","JavaFX Script","Julia","Jython","K","Kaleidoscope","Karel","Karel++","KEE","Kixtart","KIF","Kojo","Kotlin","KRC","KRL","KUKA","KRYPTON","ksh","L","L# .NET","LabVIEW","Ladder","Lagoona","LANSA","Lasso","LaTeX","Lava","LC-3","Leda","Legoscript","LIL","LilyPond","Limbo","Limnor","LINC","Lingo","Linoleum","LIS","LISA","Lisaac","Lisp","Lite-C","Lithe","Little b","Logo","Logtalk","LPC","LSE","LSL","LiveCode","LiveScript","Lua","Lucid","Lustre","LYaPAS","Lynx","M2001","M4","Machine code","MAD","MAD/I","Magik","Magma","make","Maple","MAPPER","MARK-IV","Mary","MASM Microsoft Assembly x86","Mathematica","MATLAB","Maxima","Macsyma","Max","MaxScript","Maya (MEL)","MDL","Mercury","Mesa","Metacard","Metafont","MetaL","Microcode","MicroScript","MIIS","MillScript","MIMIC","Mirah","Miranda","MIVA Script","ML","Moby","Model 204","Modelica","Modula","Modula-2","Modula-3","Mohol","MOO","Mortran","Mouse","MPD","CIL","MSL","MUMPS","NASM","NATURAL","Napier88","Neko","Nemerle","nesC","NESL","Net.Data","NetLogo","NetRexx","NewLISP","NEWP","Newspeak","NewtonScript","NGL","Nial","Nice","Nickle","Nim","NPL","Not eXactly C","Not Quite C","NSIS","Nu","NWScript","NXT-G","o:XML","Oak","Oberon","Obix","OBJ2","Object Lisp","ObjectLOGO","Object REXX","Object Pascal","Objective-C","Objective-J","Obliq","Obol","OCaml","occam","occam-π","Octave","OmniMark","Onyx","Opa","Opal","OpenCL","OpenEdge ABL","OPL","OPS5","OptimJ","Orc","ORCA/Modula-2","Oriel","Orwell","Oxygene","Oz","P#","ParaSail (programming language)","PARI/GP","Pascal","Pawn","PCASTL","PCF","PEARL","PeopleCode","Perl","PDL","PHP","Phrogram","Pico","Picolisp","Pict","Pike","PIKT","PILOT","Pipelines","Pizza","PL-11","PL/0","PL/B","PL/C","PL/I","PL/M","PL/P","PL/SQL","PL360","PLANC","Plankalkül","Planner","PLEX","PLEXIL","Plus","POP-11","PostScript","PortablE","Powerhouse","PowerBuilder","PowerShell","PPL","Processing","Processing.js","Prograph","PROIV","Prolog","PROMAL","Promela","PROSE modeling language","PROTEL","ProvideX","Pro*C","Pure","Python","Q (equational programming language)","Q (programming language from Kx Systems)","Qalb","QtScript","QuakeC","QPL","R","R++","Racket","RAPID","Rapira","Ratfiv","Ratfor","rc","REBOL","Red","Redcode","REFAL","Reia","Revolution","rex","REXX","Rlab","RobotC","ROOP","RPG","RPL","RSL","RTL/2","Ruby","RuneScript","Rust","S","S2","S3","S-Lang","S-PLUS","SA-C","SabreTalk","SAIL","SALSA","SAM76","SAS","SASL","Sather","Sawzall","SBL","Scala","Scheme","Scilab","Scratch","Script.NET","Sed","Seed7","Self","SenseTalk","SequenceL","SETL","Shift Script","SIMPOL","SIGNAL","SiMPLE","SIMSCRIPT","Simula","Simulink","SISAL","SLIP","SMALL","Smalltalk","Small Basic","SML","Snap!","SNOBOL","SPITBOL","Snowball","SOL","Span","SPARK","Speedcode","SPIN","SP/k","SPS","Squeak","Squirrel","SR","S/SL","Stackless Python","Starlogo","Strand","Stata","Stateflow","Subtext","SuperCollider","SuperTalk","Swift (Apple programming language)","Swift (parallel scripting language)","SYMPL","SyncCharts","SystemVerilog","T","TACL","TACPOL","TADS","TAL","Tcl","Tea","TECO","TELCOMP","TeX","TEX","TIE","Timber","TMG","Tom","TOM","Topspeed","TPU","Trac","TTM","T-SQL","TTCN","Turing","TUTOR","TXL","TypeScript","Turbo C++","Ubercode","UCSD Pascal","Umple","Unicon","Uniface","UNITY","Unix shell","UnrealScript","Vala","VBA","VBScript","Verilog","VHDL","Visual Basic","Visual Basic .NET","Visual DataFlex","Visual DialogScript","Visual Fortran","Visual FoxPro","Visual J++","Visual J#","Visual Objects","Visual Prolog","VSXu","Vvvv","WATFIV, WATFOR","WebDNA","WebQL","Windows PowerShell","Winbatch","Wolfram","Wyvern","X++","X#","X10","XBL","XC","XMOS architecture","xHarbour","XL","Xojo","XOTcl","XPL","XPL0","XQuery","XSB","XSLT","XPath","Xtend","Yorick","YQL","Z notation","Zeno","ZOPL","ZPL"]

            if not skill:
                message="Skill is empty"
                return Response({"message":message})
            if skill not in sample_skills:
                message="Select Skill from given"
                return Response({"message":message})
            if professional_skills.objects.filter(user=profe_user.id,skill=skill).exists():
                message="Skill is already there"
                return Response({"message":message})
            else:
                professional_skills.objects.create(user=profe_user,skill=skill)
                message="Skill added successfully"
                return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ProfessionalDeleteSkillAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            professional_obj=professional.objects.get(professional_user=request.user.id)
            skill = professional_skills.objects.get(user=professional_obj.id,id=pk)
            skill.delete()
            message="Deleted Success"

        except Exception as e:
            print(e)
            message="Failed"


        response={
            "message":message,
            "data":None
        }

        return Response(response)

class ProfessionalSettingsUploadPictureAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        data = professional.objects.get( professional_user=request.user.id)
        serializer =ProfessionalUpdateimageSerializer(data ,data=request.data,partial=True)
        if serializer.is_valid():
            try:
                if data.profile_picture == 'Null':
                    serializer.save()
                    message="Successfully updated !"
                else:
                    file_exists=os.path.exists(data.profile_picture.path)
                    if file_exists == True:
                        os.remove(data.profile_picture.path)
                    serializer.save()
                message="Successfully updated !"
                return Response({"message":message})
            except:
                return Response({"message":"Failed"})

        else:
            message=error_handle(serializer.errors)
            return Response(message)


            # data = professional.objects.get(professional_user=request.user.id)
            # try:
            #     profile_image=request.data['profile_image']
            #     _format, _dataurl =profile_image.split(';base64,')
            #     _filename, _extension   = secrets.token_hex(20), _format.split('/')[-1]
            #     try:
            #         file = ContentFile( base64.b64decode(_dataurl), name=f"{_filename}.{_extension}")
            #         if data.profile_picture == 'Null':
            #             data.profile_picture=file
            #             data.save()
            #         else:
            #             file_exists=os.path.exists(data.profile_picture.path)
            #             if file_exists == True:
            #                 os.remove(data.profile_picture.path)
            #             data.profile_picture=file
            #             data.save()
            #         message="Image successfully added"
            #     except:
            #         message="Image not added , please retry later"
            #     return Response({"message":message})
            # except:

class ProfessionalSettingsUploadResumeAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        data = professional.objects.get( professional_user=request.user.id)
        serializer =ProfessionalUpdateResumeSerializer(data ,data=request.data,partial=True)
        if serializer.is_valid():
            if data.resume == 'Null':
                serializer.save()
                message="Successfully updated... !"
            else:
                file_exists=os.path.exists(data.resume.path)
                if file_exists == True:
                    os.remove(data.resume.path)
                serializer.save()
            message="Successfully updated... !"
            return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ProfessionalFavouriteListAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            professional_data=professional.objects.get(professional_user=request.user.id)
            professional_favourite_program_data=professional_favourite_program.objects.filter(professional=professional_data.id)
            serializer=ProfessionalFavouriteProgramSerializer(professional_favourite_program_data,many=True).data

            message="Success"
        except:
            message="Failed"
            serializer=None


        response={
            "message":message,
            "data":serializer
        }
        return Response(response)



class PrefessionalFavouritePorgramAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            program_data=companyProgram.objects.get(id=pk)
            professional_data=professional.objects.get(professional_user=request.user.id)
            if professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).exists():
                professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).delete()
                message="Deleted from favourite"
            else:
                professional_data=professional.objects.get(professional_user=request.user.id)
                professional_favourite_program_data=professional_favourite_program.objects.create(professional=professional_data,program_id=program_data)
                message="added to favourite"

        except:
            message="Falied"


        response={
            "message":message,
            "data":None,
        }
        return Response(response)

class ProfessionalInformationAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        professional_obj=professional.objects.get(professional_user=request.user.id)
        try:
            professional_information_obj=professional_information.objects.get(professional=professional_obj.id)
            status=True
            message="success"
        except:
            message="failed"
            status=False
        return Response({"message":message,"status":status})

    def post(self,request,format=None):
        professional_obj=professional.objects.get(professional_user=request.user.id)
        serializer=professionalInformationSerializer(data=request.data)
        if serializer.is_valid():
            professional_information.objects.create(status=True,professional=professional_obj,country_names=serializer.data['country_names'])
            message="success"
            return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ProfessionalPaymentAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        print("reached")
        professional_data=professional.objects.get(professional_user=request.user.id)
        serializer = ProfessionalPaymentSerializer(data=request.data)
        if serializer.is_valid():
            wallet_object=professional_wallet.objects.get(professional=professional_data)
            amount=serializer.data['withdraw_amount']
            if wallet_object.amount > amount:
                total=wallet_object.amount-amount
                professional_wallet.objects.filter(professional=professional_data).update(amount=total)
                message="success"
            else:
                message="Don't have enough wallet balance"
            return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ProfessionalTestAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self, request,*args,**kwargs):
        test_obj=professional_test.objects.all()
        response={
            "data":ProfessionalTestSerializer(test_obj,many=True).data,
            "message":"success"
        }
        return Response(response)

class ProfessionalTestUpdateAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self, request):
        professional.objects.filter(professional_user=request.user).update(test_status=True)
        return Response({"message":"success"})

# class ProfessionalSettingsOptionalEmailAPIView(APIView):
#     def post(self,request,format=None):
#         user=User.objects.get(id=2)
#         ExtendUser_obj=ExtendUser.objects.get(user=user.id)
#         print(ExtendUser_obj.optional_email_token)
#         token=request.data['token']
#         if ExtendUser_obj.optional_email_token == token:
#             message="email successfully verified"
#             ExtendUser.objects.filter(user=user.id).update(optional_email_status=True)
#         else:
#             message="Enter the right token"
#         response={
#             "message":message,
#         }
#         return Response(response)

# class ProfessionalSettingsPhoneNumberVerificationAPIView(APIView):
#     def post(self,request,format=None):
#         print("reached1")
#         country=request.POST.get('country')
#         phone_number=request.POST.get('phone_number')
#         code=request.POST.get('code')
#         ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
#         if code :
#             try:
#                 ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
#                 if code == ValidateNumber_obj.code:
#                     ValidateNumber.objects.filter(user=ExtendUser_obj.id).update(status=True)
#                     message="Your phone number successfully validated"
#                 else:
#                     message="Security code doesnot match"
#             except:
#                 pass

#         else:
#             try:
#                 ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)

#             except:
#                 ValidateNumber_obj=None
#                 number=f'{country}{phone_number}'
#                 account_sid =settings.TWILIO_ACCOUNT_SID
#                 auth_token = settings.TWILIO_AUTH_TOKEN
#                 client = Client(account_sid, auth_token)
#                 validation_code=9023456
#                 try:
#                         message_obj = client.messages.create(
#                                                 body=f'Your Vulnbounty security code {validation_code}',
#                                                 from_='+13862303382',
#                                                 to=number
#                                             )
#                         ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
#                         ValidateNumber.objects.create(user=ExtendUser_obj,message_id=message_obj.sid,phone_number=number,code=validation_code)
#                         message="Security code send to given number"
#                 except:
#                     message="Something went Wrong retry again"

class UpdateUserProfileAndProfessional(APIView):
   permission_classes = [IsAuthenticated]

   def post(self, request):
        user = request.user
        profile_instance, created = UserProfile.objects.get_or_create(user=user)
        professional_instance, prof_created = professional.objects.get_or_create(professional_user=user)


        profile_serializer = UserProfileUpdateSerializer(profile_instance, data=request.data, partial=True)
        if profile_serializer.is_valid():
            profile_instance = profile_serializer.save()

            professional_serializer = UpdateProfessionalSerializer(professional_instance, data=request.data, partial=True)
            if professional_serializer.is_valid():
                professional_serializer.save()

                return Response({"message": "Profile updated successfully"})
            else:
                return Response(professional_serializer.errors, status=400)
        else:
            return Response(profile_serializer.errors, status=400)

class UserResponseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        serializer = UserResponseSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({'message': 'User responses saved successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnifiedCompanyAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            request_data = request.query_params.copy()

            # Fetch companyProgram data if 'time_range' query parameter is present
            company_programs = None
            if 'time_range' in request_data:
                # time_range = request_data.pop('time_range')
                time_range = 'week'

                if time_range in ['week', 'month', 'year']:
                    start_date_program = timezone.now() - timezone.timedelta(days=365)  # Default to showing all programs
                    if time_range == 'week':
                        start_date_program -= timezone.timedelta(days=7)
                    elif time_range == 'month':
                        start_date_program -= timezone.timedelta(days=30)
                    elif time_range == 'year':
                        start_date_program -= timezone.timedelta(days=365)

                    company_programs = companyProgram.objects.filter(created_at__gte=start_date_program)

            # Fetch company dashboard data if no 'time_range' query parameter is present
            if not company_programs:
                company_user_id = request.user.id
                company_obj = company.objects.get(company_user=company_user_id)
                submission_today = submission.objects.filter(
                    program__company=company_user_id, created_at__date=date.today()).count()
                submission_this_month = submission.objects.filter(
                    program__company=company_user_id, created_at__month=date.today().month).count()
                top_hunter = professional.objects.filter(
                    reward__gte=1).order_by("-reward")[:5]
                payment_today = payments.objects.filter(
                    transfer_from=company_obj.id, created_at__date=date.today()).aggregate(Sum('amount'))
                payment_this_month = payments.objects.filter(
                    transfer_from=company_obj.id, created_at__month=date.today().month).aggregate(Sum('amount'))

            # Prepare and return response data
            message = "success"
            response_data = {
                "message": message,
                "data": {
                    # Include companyProgram data if available
                    "company_programs": companyProgram(company_programs, many=True).data if company_programs else {},

                    # Include company dashboard data
                    "submission_today": submission_today,
                    "submission_this_month": submission_this_month,
                    "top_hunter": ProfessionalDashbordserializer(top_hunter, many=True).data,
                    "payment_today": payment_today,
                    "payment_this_month": payment_this_month
                }
            }

            return Response(response_data)

        except Exception as e:
            message = "failed"
            response = {
                "message": message,
                "data": None
            }
            return Response(response)

class CompanyProgramListAPIView(APIView):
    serializer_class = CompanyProgramSerializer
    def get_queryset(self):
        time_range = self.request.query_params.get('time_range', 'week')
        if time_range == 'week':
            start_date = timezone.now() - timezone.timedelta(days=7)
        elif time_range == 'month':
            start_date = timezone.now() - timezone.timedelta(days=30)
        elif time_range == 'year':
            start_date = timezone.now() - timezone.timedelta(days=365)
        else:
            start_date = timezone.now() - timezone.timedelta(days=365)
        queryset = companyProgram.objects.filter(created_at__gte=start_date)
        return queryset