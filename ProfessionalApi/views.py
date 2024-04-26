from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from CompanyApi.models import companyProgram,submission,ScopeEntry
from django.db.models import Q
from CompanyApi.serializers import CompanyProgramSerializer,CompanySubmissionSerializer,ScopeEntrySerializer
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
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from collections import defaultdict
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def calculateStreakforUser(user):
     streak =0
     today = datetime.now()
     start_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
     end_of_year = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
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
        streaks[submission_month] = max(streaks[submission_month], current_streak)

     return streaks


BADGES = {
    'streakBadges': [
        {'name': 'Streak Beginner', 'threshold': 3,
            'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg'},
        {'name': 'Streak Intermediate', 'threshold': 7,
            'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg'},
        {'name': 'Streak Expert', 'threshold': 12,
            'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg'},
    ],
    'submissionsBadges': [
        {'name': '5-day Streak Badge', 'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg','threshold':1},
        {'name': '10-day Streak Badge', 'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg','threshold':3},
       {'name': '15-day Streak Badge', 'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg','threshold':4},
        {'name': '20-day Streak Badge', 'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg','threshold':5},
        {'name': '100-day Streak Badge', 'image': 'https://png.pngtree.com/element_pic/00/16/07/18578cd65e6ecaa.jpg','threshold':6},
    ]
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
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    serializer_class = CompanyProgramSerializer

    def get(self, request, *args, **kwargs):
        try:
            time_range = request.GET.get('time_range', 'week')
            start_date = None

            if time_range == 'week':
                # Check if programs for this week exist
                week_programs = companyProgram.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
                if week_programs.exists():
                    start_date = timezone.now() - timezone.timedelta(days=7)
                else:
                    # If no programs for this week, use last month
                    start_date = timezone.now() - timezone.timedelta(days=30)
            elif time_range == 'month':
                # Check if programs for this month exist
                month_programs = companyProgram.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
                if month_programs.exists():
                    start_date = timezone.now() - timezone.timedelta(days=30)
                else:
                    # If no programs for this month, use last year
                    start_date = timezone.now() - timezone.timedelta(days=365)
            elif time_range == 'year':
                # Check if programs for this year exist
                year_programs = companyProgram.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=365))
                if year_programs.exists():
                    start_date = timezone.now() - timezone.timedelta(days=365)
                else:
                    # If no programs for this year, use last year
                    start_date = timezone.now() - timezone.timedelta(days=365)
            elif time_range == 'today':
                start_date = timezone.now() - timezone.timedelta(days=7)
            else:
                start_date = timezone.now() - timezone.timedelta(days=365)

            company_programs = companyProgram.objects.filter(created_at__gte=start_date)
            company_program_data = CompanyProgramSerializer(company_programs, many=True).data

            submission_today = submission.objects.filter(
                user=request.user.id,
                created_at__date=date.today()
            ).count()

            submission_this_month = submission.objects.filter(
                user=request.user.id,
                created_at__month=date.today().month
            ).count()

            leaderboard = professional.objects.filter(
                reward__gte=1
            ).order_by('-reward')[:5]

            leaderboard_data = ProfessionalDashbordserializer(leaderboard, many=True).data

            payment_today = payments.objects.filter(
                transfer_to=request.user.id,
                created_at__date=date.today()
            ).aggregate(Sum('amount'))

            payment_this_month = payments.objects.filter(
                transfer_to=request.user.id,
                created_at__month=date.today().month
            ).aggregate(Sum('amount'))

            response = {
                "message": 'success',
                "data": {
                    'user': request.user.username,

                    # Submission data
                    "submission_today": submission_today,
                    "submission_this_month": submission_this_month,

                    # Leaderboard data
                    "top_hunter": leaderboard_data,

                    # Company program data
                    "program": company_program_data,

                    # Payment data
                    "payment_today": payment_today,
                    "payment_this_month": payment_this_month
                }
            }
        except Exception as e:
            print(e)
            response = {
                "message": "Failed",
                "data": None
            }

        return Response(response)

class ProfessionalProgramAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professional_obj = professional.objects.get(professional_user=request.user)
        # professional_information_obj = professional_information.objects.get(professional=professional_obj.id)
        region = professional_obj.country

        # Fetch company programs excluding expired programs
        data = companyProgram.objects.filter(
            # (Q(region= 'all')),
            expiry_date__gte=timezone.now().date()
        )

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
        profe_user = professional.objects.get(professional_user=request.user.id)
        serializer = ProfessionalCertificatesAddSerializer(data=request.data)

        if serializer.is_valid():
            certificate_data={
               'user':profe_user,
                'certificate_name':serializer.validated_data.get(u'certificate_name'),
    'organisations':serializer.validated_data.get('organisations'),
    'issues_date':serializer.validated_data.get('issues_date'),
    'expiry_date' :serializer.validated_data.get('expiry_date'),
    'certificate_id':serializer.validated_data.get('certificate_id'),
                'certificate_url': serializer.validated_data.get('certificate_url'),

            }
            Certificate.objects.create(**certificate_data)
            response_data = {
                'message': 'Certificate added successfully',
                'certificate_data': serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListCertificatesAPIView(APIView):
    def get(self, request):
        profe_user = professional.objects.get(
            professional_user=request.user.id)
        certificates = Certificate.objects.filter(user=profe_user.id)
        serializer = ProfessionalCertificatesSerializer(certificates, many=True)
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
                "program":serializer
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

    def post(self, request):
        serializer = ProfessionalprogramSubmissionSerializer(data=request.data)

        if serializer.is_valid():
            program_id = serializer.validated_data.get('program_id')
            title = serializer.validated_data.get('title')
            report = serializer.validated_data.get('report')

            try:
                program_obj = companyProgram.objects.get(id=program_id)
            except ObjectDoesNotExist:
                return Response({"message": "Program not found"}, status=404)

            if submission.objects.filter(program=program_obj, user=request.user).exists():
                return Response({"message": "Already submitted for this program"})
            else:
                user_submission_data = {
                    'user': request.user,
                    'program': program_obj,
                    'title': title,
                    'report': report,
                    'severity': serializer.validated_data.get('severity'),
                    'description': serializer.validated_data.get('description'),
                    'impact': serializer.validated_data.get('impact'),
                    'asset': serializer.validated_data.get('asset'),
                    'weakness': serializer.validated_data.get('weakness'),
                    'status': 'pending',  # Set your default value for status
                    'payment_status': serializer.validated_data.get('payment_status'),
                    'payment_amount': serializer.validated_data.get('payment_amount'),
                    'location': serializer.validated_data.get('location'),
                }

                user_submission = submission.objects.create(**user_submission_data)

                message = "Success"
                return Response({"message": message})
        else:
            message = error_handle(serializer.errors)
            return Response({"message": message}, status=400)


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
            data=submission.objects.get(id=pk,user=request.user.id)

            response={
            "message":"Success",
            "data":{
                "submission_details_obj":CompanySubmissionSerializer(data).data
            }
            }
        except Exception as e:
            print(f"Error: {e}")
            response={
            "message":"Failed",
            "data":None
        }
        return Response(response)


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
        points[user_id] = sub['total_points']*10 + calculate_streak_points(streak)
    return points

class ProfessionalLearderAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

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
                serializer = ProfessionalDashbordserializer(professional_data)
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




class UpdateInvitationPreferenceAPIView(APIView):
    serializer_class = ProfessionalSerializer

    def post(self, request, pk=None):
        professional_instance = get_object_or_404(professional, pk=pk)
        value = request.data.get('value', None)

        if value is not None:
            professional_instance.invitation_preference = value
            professional_instance.save()
            return Response({'message': 'Invitation preference updated successfully.'})
        else:
            return Response({'error': 'Value is required to update invitation preference.'}, status=status.HTTP_400_BAD_REQUEST)

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

        try:
           user_to_follow = User.objects.get(id=follower_id)
           professional_to_follow = professional.objects.get(professional_user=user_to_follow)

        except professional.DoesNotExist:
            return Response({"message": "Professional not found"}, status=400)



        user_professional = professional.objects.get(professional_user=user)

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
        user = request.user.id
        try:
            profe_user = professional.objects.get(
                professional_user=request.user.id)
        except professional.DoesNotExist:
            return Response({"followers": []})
        # Reverse the relationship to get followers
        followers = Follower.objects.filter(professional=profe_user)
        users_following = [follower.user for follower in followers]
        serializer = AllUserSerializer(users_following, many=True)

        return Response({"following": serializer.data})


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
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            program_count = submission.objects.filter(program__company=request.user.id).count()
            professional_obj = professional.objects.get(professional_user=request.user.id)
            total_payment = payments.objects.filter(transfer_from=professional_obj.id).aggregate(Sum('amount'))
            professional_login_details_obj = professional_login_details.objects.get(professional=professional_obj)

            # try:
            #     ExtendUser_obj = ExtendUser.objects.get(user=request.user.id)
            # except ExtendUser.DoesNotExist:
            #     ExtendUser.objects.create(user=request.user.id)
            #     ExtendUser_obj = ExtendUser.objects.get(user=request.user.id)

            # try:
            #     ValidateNumber_obj = ValidateNumber.objects.get(user=ExtendUser_obj.id)
            #     validate_number_status = "True" if ValidateNumber_obj.status else "False"
            # except ValidateNumber.DoesNotExist:
            #     ValidateNumber_obj = None
            #     validate_number_status = "False"

            user_submissions = submission.objects.filter(user=request.user.id)

            # certificates_data = self.get_certificates_data(request)
            profe_user = professional.objects.get(
                professional_user=request.user.id)
            certificates_data = Certificate.objects.filter(user=profe_user.id)
            skills_data = professional_skills.objects.filter(
                user=profe_user.id)

            streaks = calculateStreakforUser(profe_user)
            streak=0
            for month, value in streaks.items():

                if value == 0:
                    streak = 0
                else:
                    streak += 1
            streak_badges = []
            submission_badges=[]
            for badge in BADGES["streakBadges"]:
                if streak >= badge['threshold']:
                    streak_badges.append(
                        {'name': badge['name'], 'image': badge['image']})

            for badge in BADGES['submissionsBadges']:
                if user_submissions.count() >= badge['threshold']:
                    submission_badges.append(
                        {'name': badge['name'], 'image': badge['image']})

            response = {
                "message": "success",
                "data": {
                    "details": ProfessionalSettingsSerializer(professional_obj).data,
                    "program_count": program_count,
                    "total_payment": total_payment,
                    "login_details": ProfessionalLoginDetailsSerializer(professional_login_details_obj).data,
                    # "ExtendUser": ProfessionalExtendedUserSerializer(ExtendUser_obj).data,
                    # "ValidateNumber": {"obj": ValidateNumber_obj, "status": validate_number_status},
                    "submission_details": CompanySubmissionSerializer(user_submissions, many=True).data,
                    "skills_data": ProfessionalSkillsSerializer(skills_data,many=True).data,
                    "certificates_data": ProfessionalCertificatesSerializer(certificates_data,many=True).data,
                    "streak":streaks,
                    "badges":{'submission_badges':submission_badges,'streak_badges':streak_badges}
                }
            }
        except Exception as e:
            response = {
                "message": "failed",
                "data": None
            }
            print(e)

        return Response(response)

    def get_certificates_data(self, request):
        # Use reverse to generate the URL for ListCertificatesAPIView
        certificates_url = reverse('list_certificates')
        client = APIClient()
        certificates_response = client.get(certificates_url)
        return certificates_response.data if certificates_response.status_code == status.HTTP_200_OK else None


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
    # permission_classes=[IsAuthenticated]
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

class UserProfileDetailsAPIView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user_submissions = submission.objects.filter(user=user_id)
            profe_user = professional.objects.get(
                professional_user=user_id)
            certificates_data = Certificate.objects.filter(user=profe_user.id)
            skills_data = professional_skills.objects.filter(
                user=profe_user.id)

            user_professional = professional.objects.get(professional_user=user_id)
            user_program_count = submission.objects.filter(program__company=user_id).count()

            total_payment = payments.objects.filter(transfer_from=user_professional.id).aggregate(Sum('amount'))

            user_professional_login_details = professional_login_details.objects.get(professional=user_professional)

            try:
                user_extend_user = ExtendUser.objects.get(user=user_id)
            except ExtendUser.DoesNotExist:
                ExtendUser.objects.create(user=user_id)
                user_extend_user = ExtendUser.objects.get(user=user_id)

            try:
                user_validate_number = ValidateNumber.objects.get(user=user_extend_user.id)
                validate_number_status = "True" if user_validate_number.status else "False"
            except ValidateNumber.DoesNotExist:
                user_validate_number = None
                validate_number_status = "False"

            streaks = calculateStreakforUser(profe_user)
            streak=0
            for month, value in streaks.items():

                if value == 0:
                    streak = 0
                else:
                    streak += 1

            streak_badges = []
            submission_badges=[]
            for badge in BADGES["streakBadges"]:
                if streak >= badge['threshold']:
                    streak_badges.append(
                        {'name': badge['name'], 'image': badge['image']})

            for badge in BADGES['submissionsBadges']:
                if user_submissions.count() >= badge['threshold']:
                    submission_badges.append(
                        {'name': badge['name'], 'image': badge['image']})

            response = {
                "message": "success",
                "data": {
                    "submissions": CompanySubmissionSerializer(user_submissions, many=True).data,
                    "skills": ProfessionalSkillsSerializer(skills_data,many=True).data,
                    "professional_details": ProfessionalSettingsSerializer(user_professional).data,
                    "program_count": user_program_count,
                    "total_payment": total_payment,
                    "login_details": ProfessionalLoginDetailsSerializer(user_professional_login_details).data,
                    "extend_user": ProfessionalExtendedUserSerializer(user_extend_user).data,
                    "validate_number": user_validate_number,
                    "streak":streaks,
                    "badges":{"streak_badges":streak_badges,"submission_badges":submission_badges},
                    "certificates_data": ProfessionalCertificatesSerializer(certificates_data, many=True).data,

                }
            }

        except Exception as e:
            response = {
                "message": "failed",
                "data": None
            }
            print(e)

        return Response(response)

class ProfessionalBankDetailCreateView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ProfessionalBankDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(professional=request.user.professional_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfessionalBankDetailRetrieveView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Explicitly use .all() to avoid issues with the related manager
        bank_details = request.user.professional_user.bank_details.all()
        serializer = ProfessionalBankDetailSerializer(bank_details, many=True)
        return Response(serializer.data)

class WithdrawMoneyFromWalletView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            amount = Decimal(request.data.get('amount'))
        except (TypeError, ValueError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            professional_wallet = ProfessionalWallet.objects.get_wallet(request.user.professional_user)
        except ProfessionalWallet.DoesNotExist:
            return Response({"error": "Professional wallet not found"}, status=status.HTTP_404_NOT_FOUND)

        if professional_wallet.balance >= amount >= 0:
            professional_wallet.balance -= amount
            professional_wallet.save()

            # Create a bank account token (use valid testing numbers)
            bank_account_token = create_stripe_bank_account_token()

            # Perform the actual payout to the professional's bank account using Stripe API
            try:
                bank_account_number = request.user.professional_user.bank_details.first().account_number
                payout = stripe.Payout.create(
                    amount=int(amount * 100),  # Amount in cents
                    currency="usd",  # Change to the appropriate currency
                    destination=bank_account_number,
                )

                # Check the status of the payout
                if payout.status == 'paid':
                    return Response({"message": "Money withdrawn successfully and added to the bank account"}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Payout failed"}, status=status.HTTP_400_BAD_REQUEST)
            except AttributeError:
                return Response({"error": "Bank details not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Invalid amount or insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)

def create_stripe_bank_account_token():
    # Use valid testing numbers
    token = stripe.Token.create(
        bank_account={
            "country": "US",
            "currency": "usd",
            "account_holder_name": "John Doe",
            "account_holder_type": "individual",
            "routing_number": "110000000",
            "account_number": "000123456789",
        },
    )
    return token.id

class WalletBalanceView(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        prof_wallet = professional_wallet.objects.get(professional = request.user.professional_user)
        prof_wallet_history = professional_wallet_history.objects.get(professional=request.user.professional_user)
        if professional_wallet:
            wallet = ProfessionalWalletSerializer(prof_wallet).data
            walletHistory = ProfessionalWalletHistorySerializer(prof_wallet_history).data
            response = {
                "data":{
                    "wallet":wallet,
                    "walletHistory":walletHistory
                }
            }
            return Response(response,status=status.HTTP_200_OK)
        else:
            return Response({"error": "Professional wallet not found"}, status=status.HTTP_404_NOT_FOUND)

class YourView(APIView):

    def post(self, request, *args, **kwargs):# Create a mutable copy of the QueryDict
        serializer = UserSelectionSerializer(data=request.data)
        if serializer.is_valid():
            profe_user = professional.objects.get(
                professional_user=request.user.id)
            serializer.save(user=profe_user)

            profe_user.questions_completed = True
            profe_user.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        professional_instance, created = professional.objects.get_or_create(
            professional_user=request.user.id)

        user_selections = UserSelection.objects.filter(
            user=professional_instance).get()
        serializer = UserSelectionSerializer(user_selections)
        return Response(serializer.data)
class UserSelectionUpdateView(APIView):
    def put(self, request, pk, *args, **kwargs):
        try:
            user_selection = UserSelection.objects.get(pk=pk)
        except UserSelection.DoesNotExist:
            return Response({"message": "User selection not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSelectionSerializer(
            user_selection, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StreakAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve the current user's streak without updating it
        instance, created = Streak.objects.get_or_create(user=request.user)

        serializer = StreakSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Update the streak when a POST request is received
        instance, created = Streak.objects.get_or_create(user=request.user)
        instance.update_streak()
        serializer = StreakSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomScopeEntryListCreateView(APIView):
    serializer_class = ScopeEntrySerializer

    def get(self, request, *args, **kwargs):
        program_id = self.kwargs['program_id']
        scope_entries = ScopeEntry.objects.filter(program_id=program_id)
        serializer = self.serializer_class(scope_entries, many=True)
        return Response(serializer.data)


class CompanyProgramDetailsAPIViewinProfessional(APIView):
    renderer_classes = [UserRender]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user

        try:
            program_obj = companyProgram.objects.get(company=user, id=pk)
            program_serializer = CompanyProgramSerializer(program_obj)
            data = {
                "program": program_serializer.data
            }
            response = {
                "data": data
            }
        except companyProgram.DoesNotExist:
            response = {
                "message": "Program does not exist"
            }

        return Response(response)
