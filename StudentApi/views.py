from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from StudentApi.models import *
from SubmissionApi.models import *
from ProgramsApi.models import *
from CompanyApi.models import *
from datetime import date
from django.db.models import Sum
from StudentApi.serializers import *
from ProgramsApi.serializers import *
from SubmissionApi.serializers import *
from CompanyApi.serializers import *
import json 
from django.http import JsonResponse
from SubmissionApi.forms import *
from ChatApi.models import *
from ChatApi.serializers import *
import stripe
from django.contrib import messages as message
from ExtendUserApi.models import ExtendUser,ValidateNumber
from django.contrib.auth import authenticate, login, logout
import uuid
import os 
from django.core.files.base import ContentFile
from CompanyApi.forms import *

from asyncio.windows_events import NULL
import code
import profile
from typing import Optional
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib import messages as message
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import re
from django.db.models import Q
from twilio.rest import Client
from django.core.files.base import ContentFile
import base64, secrets
from StudentApi.helpers import send_email_verification_mail
import uuid
from .serializers import *
from django.http import JsonResponse
from ProfessionalApi.forms import *
from ExtendUserApi.serializers import *
import requests
from CompanyApi.models import *
from CompanyApi.serializers import CompanyProgramSerializer
# Create your views here.
 # --------------------- DASHBOARD ------------------------------
user_id=4

user=User.objects.get(id=user_id)


class ProfessionalRegisterAPIView(APIView):
     def post(self,request):
        serializer=StudentRegisterSdrializer(data=request.data)
        print(request.data)
        client_key=request.data('g-recaptcha-response')
        secret_key=settings.RECAPTCHA_SECRET_KEY
        captcha_data={
                "secret":secret_key,
                "response":client_key
            }
        response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
        response=json.loads(response_data.text)
        verify=response['success']
        print(f'verify is = {verify}')
        verify=True
        if verify == True:
            terms_and_policy=request.data('terms_and_policy')
            if not terms_and_policy == 'checked':
                message="please tick the privacy policy and terms"
            else:
                if serializer.is_valid(raise_exception=True):
                    password=serializer.cleaned_data.get('password')
                    confirm_password=serializer.cleaned_data.get('confirm_password')
                    if password != confirm_password:
                        message="password and confirm pasword didn't match"
                        return Response({"message":message})
                    token = str(uuid.uuid4())
                    user=serializer.save(commit=False)
                    user.password=make_password(request.POST['password'])
                    user.username=serializer.cleaned_data['username']
                    user.email_verification_token=  token
                    user.save()
                    company_obj = company.objects.create(company_user=user,email_verification_token= token,terms_and_policy=True)
                    if company_obj:
                        company_wallet.objects.create(company=company_obj)
                        send_email_verification_mail(request,user.email,token)
                        messsage='Account created Successfully ! verify your email'
                    else:
                        message='Account not created retry again'
                    return Response({"path":"ifreached"})
                    
                else:
                    print("elsereached")
                    return Response({"path":"elsereached"})
        else:
            message="reCAPTCHA not verifyied"
        return Response({"message":messsage}) 
  




class DashboardView(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        profile=Student.objects.get(student_user=user)
        serializers=StudentSerializer(profile)
        data=serializers.data
        submission_today=submission.objects.filter(user=request.user.id,created_at__date=date.today()).count()
        submission_this_month=submission.objects.filter(user=request.user.id,created_at__month=date.today().month).count()
        leaderboard= Student.objects.filter(reward__gte=1).order_by('-reward')[:5]
        serializers=StudentSerializer(leaderboard,many=True)
        data1=serializers.data
        program=companyProgram.objects.filter(created_at=date.today())[:5]
        payment_today = payments.objects.filter(transfer_to=request.user.id,created_at__date=date.today()).aggregate(Sum('amount'))
        payment_this_month=payments.objects.filter(transfer_to = request.user.id,created_at__month=date.today().month).aggregate(Sum('amount'))
        context={
            'user':request.user.username,
            'profile':data,
            "submission_today":submission_today,
            "submission_this_month":submission_this_month,
            "leaderboard":data1,
            "program":CompanyProgramSerializer(program,many=True).data,
             "payment_today":payment_today,
            "payment_this_month":payment_this_month
            }

        return Response(context)

       
# --------------------- PROGRAM --------------------------------     

class ProgramView(APIView):
    def get(self,request,format=None):
        context={}
        user=User.objects.get(id=2)
        student_obj=Student.objects.get(student_user=user)
        serializers=StudentSerializer(student_obj)
        student_information_obj=student_information.objects.get(student=student_obj)
        serializers=student_informationSerializer(student_information_obj)
        stud_info_data=serializers.data
        student_country=student_information_obj.country_names
        startdate=request.POST.get('startdate')
        enddate=request.POST.get('enddate')
        if not startdate or not enddate:
            print('Start date and End date is requird')
        print(startdate,enddate)
        data1=programs.objects.get(id=2)
        serializers=programsSerializer(data1)
        data_response=serializers.data
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country),created_at__range=(startdate,enddate))
        print(data.count())
        if data.count() == 0:
            print('Not found any program in between the given date')
        context={"data":data,
        "student_country":student_country,}
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country))
        student_data=Student.objects.get(student_user=user)
        context_data={
            "stud info":stud_info_data,
            "Program details":data_response,
            "student_country":student_country,
        
        }
        return Response(context_data)

    def post(self,request,format=None):
        user=User.objects.get(id=2)
        student_obj=Student.objects.get(student_user=user)
        student_information_obj=student_information.objects.get(student=student_obj)
        serializers=student_informationSerializer(student_information_obj)
        student_country=student_information_obj.country_names
        startdate=request.POST.get('startdate')
        enddate=request.POST.get('enddate')
        if not startdate or not enddate:
            print('Start date and End date is requird')
        print(startdate,enddate)
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country),created_at__range=(startdate,enddate))
        print(data.count())
        if data.count() == 0:
            print('Not found any program in between the given date')
        context={"data":data,
        "student_country":student_country,}
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country))
        student_data=Student.objects.get(student_user=user)
        context_data={"data":data,
            "student_country":student_country,
        
        }
        return Response(serializers.data)


class Programfilter(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        student_obj=Student.objects.get(student_user=user)
        student_information_obj=student_information.objects.get(student=student_obj)
        serializers=student_informationSerializer(student_information_obj)
        student_country=student_information_obj.country_names
        startdate=request.POST.get('startdate')
        enddate=request.POST.get('enddate')
        if not startdate or not enddate:
            print('Start date and End date is requird')
        print(startdate,enddate)
        data1=programs.objects.get(id=2)
        serializers=programsSerializer(data1)
        data_response=serializers.data
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country),created_at__range=(startdate,enddate))
        print(data.count())
        if data.count() == 0:
            print('Not found any program in between the given date')
        context={
            "data1":data_response,
            "data":data,
        "student_country":student_country,}
        data=programs.objects.all().filter(Q(region ='all') | Q(region = student_country))
        student_data=Student.objects.get(student_user=user)
        return Response(context)

class Program_details_view(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        Program_id=programs.objects.get(id=1)
        serializers=programsSerializer(Program_id)
        data=serializers.data
        query=submission.objects.filter(program=Program_id,user=user)
        serializers=submissionSerializer(query,many=True)
        response=serializers.data
        context={
            'data':data,
            'response':response
        }
        return Response(context)

# --------------------- SUBMISSION -----------------------------

class  SubmissionView(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        all_submission=submission.objects.filter(user=user)
        serializers=submissionSerializer(all_submission,many=True)
        data=serializers.data
        pending_submission=submission.objects.filter(user=user,status="pending")
        serializers=submissionSerializer(pending_submission,many=True)
        data1=serializers.data
        rejected_submission=submission.objects.filter(user=user,status="rejected")
        serializers=submissionSerializer(rejected_submission,many=True)
        data2=serializers.data
        accepted_submission=submission.objects.filter(user=user,status="accepted")
        serializers=submissionSerializer(accepted_submission,many=True)
        data3=serializers.data
        completed_submission = submission.objects.filter(user=user,status="completed")
        serializers=submissionSerializer(completed_submission,many=True)
        data4=serializers.data
        response={
            "all_submission":data,
            "pending_submission":data1,
            "accepted_submission":data2,
            "rejected_submission":data3,
            'completed_submission':data4
            }
        return Response(response)

class  Student_submission_details_view(APIView): 
    def get(self,request,format=None): 
        user=User.objects.get(id=2)
        program_id=programs.objects.get(id=1)
        data=submission.objects.get(program=program_id,user=user)
        serializers=submissionSerializer(data)
        response=serializers.data
        return Response(response)
       
class Submit_program_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        submit_program=programs.objects.get(id=1)
        serializers=programsSerializer(submit_program)
        serializers_data=serializers.data
        if serializers.is_valid():
            serializers.save()
        return Response({"message":"progem submitted successfully !"})
                

class Chat_view(APIView):
    def post(self,request,format=None):
        user=submission.objects.get(id=1)
        if request.method=='POST' and 'chat_send' in request.POST:
            text=request.POST.get('text')
            
            sender_id=request.user.id
            data=submission.objects.get(id=user)
            serializers=submissionSerializer(data)
            response=serializers.data
            receiver_id=data.program.company.id
            message=messages.objects.create(submission_id=user,sender_id=sender_id,receiver_id=receiver_id,text=text)
            serializers=messagesSerializer(message)
            msg=serializers.data
            response_data={
                'response':response,
                'msg':msg
            }
            return Response(response_data)
        data=messages.objects.filter(submission_id=user).order_by('created_at')
        serializers=messagesSerializer(data,many=True)
        data1=serializers.data
        receiver_data=submission.objects.get(id=user)
        serializers=submissionSerializer(receiver_data)
        data2=serializers.data
        context={
            "data":response,
            "submission_id":data1,
            "receiver_data":data2
        }
        return Response(context)

# stripe.api_key=settings.STRIPE_SECRET_KEY
class Payment_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        if request.method=="POST" and 'student_withdraw' in request.POST:
            print("reached")
            host = request.get_host()
            student_data=Student.objects.get(student_user=user)
            serializers=StudentSerializer(student_data)
            stud_data=serializers.data
            stud_id=student_data.id
            student_wallet_data=student_wallet.objects.get(student=stud_id)
            serializers=student_walletSerializer(student_wallet_data)
            stud_wallet_data=serializers.data
            try:
                amount=int(request.POST.get('amount'))
            except:
                return Response({"message":"enter a valid amount"})
            if not (10 < amount <1000 ) :
                return Response({"message":"The amount should be in between 10 and 1000 "})
            if not student_wallet_data.amount >= amount:
                return Response({"message":"Don't have this much amount in your wallet"})

            checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data':{
                        'currency':'inr',
                        'unit_amount':amount*100,
                        'product_data':{
                            "name":"sarath"
                        }
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url="http://{}/student/payment_success/{}".format(host,amount),
            cancel_url="http://"+host+'/student/payment_cancel',
            )
            
            # return redirect(checkout_session.url, code=303)
        student_data=Student.objects.get(student_user=user)
        serializers=StudentSerializer(student_data)
        data=serializers.data
        student_wallet_data=student_wallet.objects.get(student=stud_id)
        serializers=student_walletSerializer(student_wallet_data)
        data1=serializers.data
        transaction=payments.objects.filter(transfer_to=user)
        serializers=paymentsSerializer(transaction,many=True)
        transaction_data=serializers.data
        wallet_tranaction=student_wallet_history.objects.filter(student=stud_id)
        serializers=student_wallet_historySerializer(wallet_tranaction,many=True)
        wallet_tranaction_data=serializers.data

        print(wallet_tranaction)
        context={
            "student_wallet_data": data1,
            "transaction":transaction_data,
            "wallet_tranaction":wallet_tranaction_data
        }
        
        return Response(context)


class Payment_success_view(APIView):
    def get(self,request,amount):
        user=User.objects.get(id=2) 
        student_obj=Student.objects.get(student_user=user)
        serializers=StudentSerializer(student_obj)
        student_obj_data=serializers.data
        print(student_obj.id)
        student_wallet_obj=student_wallet.objects.get(student=student_obj)
        serializers=student_walletSerializer(student_wallet_obj)
        student_wallet_obj_data=serializers.data
        total_amount=student_wallet_obj.amount - int(amount)
        wallet_history=student_wallet_history.objects.create(student=student_obj,amount=int(amount),description="withdraw from wallet",status='db')
        data={
            'student_obj_data':student_obj_data,
            'student_wallet_obj_data' :student_wallet_obj_data,
        }
        return Response(data)

# --------------------- LEADERBOARD ----------------------------

class Leader_board_view(APIView):
    def get(self,request,format=None):
        data = Student.objects.filter(reward__gte=1).order_by('-reward')
        serializers=StudentSerializer(data,many=True)
        serializers_data=serializers.data
        return Response(serializers_data)

class  Leaderboard_detail_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        data=Student.objects.get(id=id)
        serializers=StudentSerializer(data)
        response=serializers.data
        return Response(response)
        
# --------------------- PROFILE --------------------------------


    # 
    #CHANGING FIRST_NAME AND LAST_NAME AND PROFILE DESCRIPTION
class Profile_setting(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        try:
            first_name=request.POST['first_name']
            last_name=request.POST['last_name']
            profile_description=request.POST.get('profile_description')
            user_obj=User.objects.filter(id=user)
            serializers=UserSerializer(user_obj,many=True)
            user_data=serializers.data
            stud=Student.objects.filter(student_user = request.user).update(profile_description=profile_description)
            serializers=StudentSerializer(stud,many=True)
            stud_data=serializers.data
            message.success(request,'Successfully updated !')
            form=Profile_Setting_Form()
            context={
                "user_data":user_data,
                "stud_data":stud_data,
            }
            return Response(context)
        except Exception as e:
            print(e)
        return Response({"meassge":"Successfully updated !"})


#CHANGINGING USERNAME AND EMAIL USING PASSWORD       
class Update_Password(APIView):
    def post(self,request):    
            try:
                regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
                print("reached_up")
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                # user_obj=User.objects.filter(id=request.user.id)
                if not username or not email or not password:
                    return Response({"meassge":"Fields should not empty"})
                else:
                    if not re.search(regex, username):
                        return Response({"meassge":"Allowed are alphabet,number and apostrophe"})
                user = authenticate(
                    request, username=request.user.username, password=password)
                if user is not None:
                    print("reached in user is not")
                    if request.user.username != username:
                        print("reached in user is not if")
                        username_query=User.objects.filter(username=username)
                        serializers=UserSerializer(username_query,many=True)
                        username_data=serializers.data
                        if username_data.exists():
                            print("filter")
                        else:
                            user_query=User.objects.filter(id=user) #.update(username=username)
                            serializers=UserSerializer(user_query,many=True)
                            user_query_data=serializers.data
                            message.success(request,'Username successfully updated !')
                    ExtendUser_obj=ExtendUser.objects.get(user=user)
                    serializers=ExtendUserSerializer(ExtendUser_obj)
                    ExtendUser_data=serializers.data
                    if ExtendUser_data.optional_email != email:
                        email= User.objects.filter(email=email)
                        serializers=UserSerializer(email,many=True)
                        email_data=serializers.data
                        Extendemail=ExtendUser.objects.filter(optional_email=email)
                        serializers=ExtendUserSerializer(Extendemail,many=True)
                        Extendemail_data=serializers.data
                        if email_data.exists() or Extendemail_data.exists():
                            print("reached in email2")
                        else:
                            token = str(uuid.uuid4())
                            print("reached in email3")
                            try:
                                ExtendUser_obj= ExtendUser.objects.get(user=user)
                                serializers=ExtendUserSerializer(ExtendUser_obj)
                                ExtendUser_obj_data=serializers.data
                                if email_data != email !=Extendemail_data: #.optional_email
                                    ExUser=ExtendUser.objects.filter(user=user) #.update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                    serializers=ExtendUserSerializer(ExUser,many=True)
                                    ExUser_data=serializers.data
                                    message.success(request,'Email successfully updated !')
                                    send_email_verification_mail(email,token)
                                else:
                                    message.warning(request,'You already added this Email')
                            except Exception as e:
                                print(e)
                                ExUser_create=ExtendUser.objects.create(user=request.user,optional_email=email,optional_email_token=token)
                                serializers=ExtendUserSerializer(ExUser_create)
                                ExUser_create_data=serializers.data
                                send_email_verification_mail(email,token)
                                message.success(request,'Email successfully Added !')
                                pass
                
                else:
                    message.error(request,'Password doesnot match')
            except Exception as e:
                print(e)

            return Response({"meassage":"Updated Successfully"})


# ADDING SKILLS AND INTSEREST 
class Add_Skills(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        skill=request.POST.get('skill')
        if not skill:
            return Response({"message":"skill is empty"})
        data = student_skills.objects.create(user=user,skill=skill)
        serializers=student_skillsSerializer(data)
        skill_response=serializers.data
        message.success(request,"Skill added successfully !")
        return Response(skill_response)

 # CHANGING IMAGES
class Update_img(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        data_profile=serializers.data
        try:
            profile_image=request.POST.get('profile_image')
            _format, _dataurl =profile_image.split(';base64,')
            _filename, _extension   = secrets.token_hex(20), _format.split('/')[-1]
            try:
                file = ContentFile( base64.b64decode(_dataurl), name=f"{_filename}.{_extension}")
                if data_profile.profile_picture == 'Null':
                    serializers.profile_picture=file
                    serializers.save()
                else:
                    file_exists=os.path.exists(data_profile.profile_picture.path)
                    if file_exists == True:
                        os.remove(data_profile.profile_picture.path)
                    data_profile.profile_picture=file
                    serializers.save()
                
                message.success(request,"Image successfully added")
                return Response({"message":"Image successfully added"})
            except:
                return Response({"message":"Image not added , please retry later"})
        except:
                print("Image is empty")
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        data_response=serializers.data
        if data.profile_picture == 'Null':
            # form.save()
            # serializers.save()
            print("image is null")
        else:
            file_exists=os.path.exists(data.profile_picture.path)
            if file_exists == True:
                os.remove(data.profile_picture.path)
                
        return Response({"message":"Image successfully added"})


        
# ADDING AND  UPDATING  RESUME 
class Update_resume(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        serializers_data=serializers.data
        form = resume_Form(request.POST, request.FILES, instance=data)
        print(data.resume.url)
        if not request.FILES:
            return Response({"message":"Field should not be empty"})
        if form.is_valid():
            data = Student.objects.get(student_user=user)
            if data.profile_picture == 'Null':
                data.save()
            else:
                file_exists=os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
                serializers.save()
            return Response({"message":"Resume successfully updated !"})

        return Response(serializers_data)

# UPDATE THE PASSWORD USING OLD PASSWORD

class Update_Old_Password(APIView):
    def post(self,request):
        password_1=request.POST.get('password1')
        password_2=request.POST.get('password2')
        password_3=request.POST.get('password3')
        if not password_1 or not password_2 or not password_3:
            return Response({"message":"Field should not be empty"})
        user = authenticate(request, username=request.user.username, password=password_1) 
        if user is not None:
            if password_2==password_3:
                password=make_password(password_2)
                userpw=User.objects.filter(id=user).update(password=password)
                user =authenticate(username=request.user.username, password=password)
                login(request, user)
                data={
                    "user password":userpw
                }
                return Response(data)
            else:
                print("New password and confirm password not match")
                return Response({"message":"New password and confirm password not match"})

        else:
            print("Old password not match")
            return Response({"message":"Old password not match"})   
        

# Optional email verification

class Email_verification(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        ExtendUser_obj=ExtendUser.objects.get(user=user,id=1)
        serializers=ExtendUserSerializer(ExtendUser_obj)
        Extend_data=serializers.data
        token=request.POST.get('token')
        return Response(Extend_data) 

    # phone number validation 
class Phone_validation(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        print("reached1")
        country=request.POST.get('country')
        phone_number=request.POST.get('phone_number')
        code=request.POST.get('code')
        ExtendUser_obj=ExtendUser.objects.get(user=user,id=1)
        serializers=ExtendUserSerializer(ExtendUser_obj)
        data=serializers.data
        if code :
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=user,id=1)
                serializers=ValidateNumberSerializer(ValidateNumber_obj)
                ValidateNumber_data=serializers.data
                if code == ValidateNumber_data.code:
                    ValidateNum=ValidateNumber.objects.filter(user=ExtendUser_obj.id) #.update(status=True)
                    serializers=ValidateNumberSerializer(ValidateNum,many=True)
                    ValidateNum_data=serializers.data
                    return Response(ValidateNum_data)
                else:
                    print("Security code doesnot match")
            except:
                pass

        else:
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=user,id=1)
                serializers=ValidateNumberSerializer(ValidateNumber_obj)
                Valid_data=serializers.data
                return Response(Valid_data)

            except:
                ValidateNumber_obj=NULL
                number=f'{country}{phone_number}'
                account_sid =settings.TWILIO_ACCOUNT_SID 
                auth_token = settings.TWILIO_AUTH_TOKEN
                client = Client(account_sid, auth_token)
                validation_code=9023456
                try:
                        message_obj = client.messages.create(
                                                body=f'Your Vulnbounty security code {validation_code}',
                                                from_='+13862303382',
                                                to=number
                                            )
                        ExtendUser_obj=ExtendUser.objects.get(user=user)
                        serializers=ExtendUserSerializer(ExtendUser_obj)
                        Extend_data=serializers.data
                        ValidateNumber.objects.create(user=Extend_data,message_id=message_obj.sid,phone_number=number,code=validation_code)
                        return Response(Extend_data)
                except:
                    print("Something went Wrong retry again")
            
        
            print("code is NOne")
        print(code)
        return Response({"message":"phone in validated"})


class Privacy_setting_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        response=serializers.data
        form = Profile_Setting_Form(instance=response)
        form = Profile_Setting_Form(request.POST, instance=data)
        if form.is_valid():
            serializers.save()
            return Response(response)


class Delete_skills_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        # skill_id=skills.objects.get(id=1)
        if student_skills.objects.filter(id=id).exists():
            print("id id exists")
            skill = student_skills.objects.get(id=id).delete() # skill_id
            print(id)
            return Response({"message":"deleted successfully"})
        else:
            print("in else condition")
            return Response({"message ": "skill not found "})

# --------------------- LOGOUT ---------------------------------

class Logout_view(APIView):
    def post(self,request):
        try:
            logout(request)
        except:
            pass
        return  Response({"message":"Logout successfully"})
# --------------------- INFORMATION ---------------------------

class Student_infromation_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        form= Information_From()
        student_obj=Student.objects.get(student_user=user.id)
        try:
            student_information_obj=student_information.objects.get(student=user)
            serializers=student_informationSerializer(student_information_obj)
            info_data=serializers.data
            status=True
        except:
            status=False
        if request.method == 'POST' and 'Add' in request.POST:
            print('reached')
            form= Information_From(request.POST)
            if form.is_valid():
                print("form valid")
                student_obj=Student.objects.get(student_user=user.id)
                form=form.save(commit=False)
                form.status=True
                form.student=student_obj
                serializers.save()
                return Response(info_data)

# --------------------- END ------------------------------------




# STUDENT SETTING START HERE


# ---------------------------PRIVACY SETTINGS ENDS HERE----------------------------
# ---------------------------LEADER BOARD START HERE ------------------------------

# ---------------------------LEADER BOARD START HERE ------------------------------

# --------------------------PROGRAMS DETAILS -------------------------------------


# ----------------------------------PROGRAM DETAILS END HERE----------------------

# ----------------------------- student_favourite_program_view ------------------------------

class Student_favourite_program_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        program_data=programs.objects.get(id=id)
        student_data=Student.objects.get(student_user=user.id)
        if student_favourite_programs.objects.filter(student=student_data,program_id=program_data).exists():
            student_favourite_programs.objects.filter(student=student_data).delete() #,program_id=program_data
            return Response({"message":"student favourite program deleted"})
        else:
            program_data=programs.objects.get(id=id)
            student_data=Student.objects.get(student_user=user.id)
            student_favourite_program_data=student_favourite_programs.objects.create(student=student_data,program_id=program_data)
            return Response({"message":"student favourite program  created "})


          
class Student_favourite_program_list_view(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        student_data=Student.objects.get(student_user=user.id)
        serializers=StudentSerializer(student_data)
        stud_data=serializers.data
        student_favourite_program_data=student_favourite_programs.objects.filter(student=user.id)
        serializers=student_favourite_programSerializer(student_favourite_program_data,many=True)
        data=serializers.data
        context={
            "student_favourite_program_data":data,
        
        }
        return Response(context)

        