
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CompanyRegisterSerializer,CompanyProgramSerializer,CompanySubmissionSerializer,CompanyProfessionalLeaderBoardSerializer,CompanyStudentLeaderBoardSerializer,ComapnyImageUploadSerializer,CompanySettingsSerializer,CompanyLoginDetailsSerializer,CompanyExtendedUserSerializer,CompanyCreateProgramSerializer,CompanyCreateProgramInScopeSerializer,CompanyCreateProgramRewardSerializer,CompanyCreateProgramSaveSerializer,CompanyCreateProgramOutScopeSerializer
from .serializers import CompanyChangeNameSerializer,CompanyChangeUserNameSerializer,CompanyUpdatePasswordSerializer
from .models import company,companyProgram,submission,payments,company_login_details,company_wallet
from django.contrib.auth.models import User
from datetime import date
from django.db.models import Sum
from StudentApi.models import Student
from ProfessionalApi.models import professional
import re
from twilio.rest import Client
from .helpers import send_email_verification_mail
import uuid
import stripe
from django.conf import settings
import os
from django.contrib.auth import authenticate, login, logout
from MainApi.models import ExtendUser,ValidateNumber,messages
from django.contrib.auth.hashers import make_password
import requests
import json

user_id=3
user=User.objects.get(id=user_id)

class CompanyRegisterAPIView(APIView):
    def post(self,request):
        serializer=CompanyRegisterSerializer(data=request.data)
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
class CompanyDashboardAPIView(APIView):
    def get(self,request):
        print(request.user.id)
        try:
            company_obj=company.objects.get(company_user=user_id)
            submission_today=submission.objects.filter(program__company=request.user.id,created_at__date=date.today()).count()
            submission_this_month=submission.objects.filter(program__company=request.user.id,created_at__month=date.today().month).count()
            top_hunter=professional.objects.filter(reward__gte=1).order_by("-reward")[:5]
            payment_today = payments.objects.filter(transfer_from=company_obj.id,created_at__date=date.today()).aggregate(Sum('amount'))
            payment_this_month=payments.objects.filter(transfer_from = company_obj.id,created_at__month=date.today().month).aggregate(Sum('amount'))
            message="success"
            response={
                "message":message,
                "data":{
                    "submission_today":submission_today,
                    "submission_this_month":submission_this_month,
                    "top_hunter":CompanyProfessionalLeaderBoardSerializer(top_hunter,many=True).data,
                    "payment_today":payment_today,
                    "payment_this_month":payment_this_month
                }
                

            }
            return Response(response)
        except Exception as e:
            message="failed"
            response={
                "message":message
            }
            return Response(response)      
class CompanyProgramAPIView(APIView):
    def get(self,request):
        user=User.objects.get(id=user_id) 
        program_obj=companyProgram.objects.filter(company=user)
        response={
            "message":"success",
            "data":{
          "programs":CompanyProgramSerializer(program_obj,many=True).data
        }
        }
        return Response(response)

    def post(self,request):
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
        verify=True
        if verify == True:
            serializer=CompanyCreateProgramSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                slug=request.data['slug']
                title=request.data['title']
                introduction=request.data['introduction']
                vulnerability_concerns= request.data['vulnerability']
                target=request.data['target']
                scope_type=request.data['scope_type']
                out_scope_target=request.data['out_target']
                visibility=request.data['visibility']
                p1_min=int(request.data['p1_min'])
                p1_max=int(request.data['p1_max'])
                p2_min=int(request.data['p2_min'])
                p2_max=int(request.data['p2_max'])
                p3_min=int(request.data['p3_min'])
                p3_max=int(request.data['p3_max'])
                p4_min=int(request.data['p4_min'])
                p4_max=int(request.data['p4_max'])
                p5_min=int(request.data['p5_min'])
                p5_max=int(request.data['p5_max'])
                try:
                    max_reward=request.data['max_reward']
                except:
                    max_reward=None
                    pass
                if not max_reward:
                    if not p1_min>0 or not p1_max>0 or not p2_min>0 or not p2_max>0 or not p3_min>0 or not p3_max>0 or not p4_min>0 or not p4_max>0 or not p5_min>0 or not p5_max >0:
                        return Response({"message":"Rewards should be positive"})
                    reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max]
                else:
                    if not p1_min > 0 or not p1_max > 0 or not p2_min > 0 or not p2_max > 0 or not p3_min > 0 or not p3_max > 0 or not p4_min > 0 or not p4_max > 0 or not p5_min > 0 or not p5_max > 0 or not int(max_reward) > 0:
                        return Response({"message":"Rewards should be positive"})
                    reward_list=[p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max,int(max_reward)]
                reward_list_copy=reward_list[:]
                reward_list_copy.sort()
                if reward_list != reward_list_copy:
                    return Response({"message":'The reward should be in increasing order'})

                in_scope=CompanyCreateProgramInScopeSerializer(data=request.data)
                reward=CompanyCreateProgramRewardSerializer(data=request.data)
                
                out_scope=CompanyCreateProgramOutScopeSerializer(data=request.data)
                

                if in_scope.is_valid(raise_exception=True) and out_scope.is_valid(raise_exception=True):
                    if reward.is_valid(raise_exception=True):
                        if  not max_reward: 
                            max_reward=None
                        reward.max_reward = max_reward
                    else:
                        return Response({"message":'Something went wrong with reward'})
                    
                    program=CompanyCreateProgramSaveSerializer(data=request.data)
                    if program.is_valid(raise_exception=True):
                        try:
                            visibility=request.data['visibility']
                        except:
                            visibility="G"                    
                        if visibility == "R":
                            region=request.data['region']
                        else:
                            region='all'
                        print(user.id)
                        program.company_id=user
                        program.in_scope=in_scope.save()
                        program.out_scope=out_scope.save()
                        program.rewards=reward.save()
                        program.region=region
                        program.save()
                        message="Program created successfully"
                    else:
                        message='Something went wrong creating program'
                    
                else:
                    return Response({"message":'Something went wrong with in_scope or out_scope'})
              
            else:
                message='Something went wrong creating program'
        else:
            message.error(request,"reCAPTCHA not verifyied")
            
            # print(title,slug,introduction,vulnerability_concerns,target,scope_type,out_scope_target,visibility,p1_min,p1_max,p2_min,p2_max,p3_min,p3_max,p4_min,p4_max,p5_min,p5_max)

            
            
                
           
                
            


            
                
            

           
        
    
        context={
        "in_scope":in_scope,
        "out_scope":out_scope,
        "program":program,
        "reward":reward,
        "values":values
        }
        return render(request,"Company/program/index.html",context)

 
class CompanyProgramDetailsAPIView(APIView):
    def get(self,request,pk):
        user=User.objects.get(id=user_id) 
        if companyProgram.objects.filter(company=user).exists():
            program_obj=companyProgram.objects.get(company=user,id=pk)
            program_serializer=CompanyProgramSerializer(program_obj)
            data={
                "program":program_serializer.data
            }
            response={
                "data":data
            }
        else:
             response={
                "message":"Program does not exits"
            }

        return Response(response)

class CompanyDeleteProgramAPIView(APIView):
    def get(self,request,pk):
        print(pk)
        try:
            companyProgram.objects.get(company=user,id=pk).delete()
            response={
                "message":"Deleted Successfully"
            }

        except  Exception as e: 
            print(e)
            response={
                "message":"Program Already Deleted"
            }
             
        return Response(response)

class CompanySubmissionAPIView(APIView):
    def get(self,request):
        print(user)
        all_submission=submission.objects.filter(program_id__company=user.id)
        pending_submission=submission.objects.filter(program_id__company=user,status='pending')
        accepted_submission=submission.objects.filter(program_id__company=user,status='accepted')
        rejected_submission=submission.objects.filter(program_id__company=user,status='rejected')
        completed_submission=submission.objects.filter(program_id__company=user,status='completed')
        
        data={
            "all_submission":CompanySubmissionSerializer(all_submission,many=True).data,
            "pending_submission":CompanySubmissionSerializer(pending_submission,many=True).data,
            "accepted_submission":CompanySubmissionSerializer(accepted_submission,many=True).data,
            "rejected_submission":CompanySubmissionSerializer(rejected_submission,many=True).data,
            "completed_submission":CompanySubmissionSerializer(completed_submission,many=True).data,
            }
        response={
            "message":"success",
            "data":data
        }
        return Response(response)
   
class CompanySubmissionDetailsAPIView(APIView):
    def get(self,request,pk):
        try:
            submission_obj=submission.objects.get(program__company=user.id ,id=pk)
            response={
                "message":"success",
            "data":{
                "submission_obj":CompanySubmissionSerializer(submission_obj).data
            }
                        }
        except Exception as e:
            print(e)
            response={
            "message":"could not find submission"
        }
        return Response(response)


class CompanySubmissionRejectAPIView(APIView):
    def get(self,request,pk):
        if submission.objects.filter(program__company=user.id,id=pk).exists():
            submission.objects.filter(program__company=user.id,id=pk).update(status="rejected")
            response={
                "message":"Submission Rejected"
            }
        else:
             response={
                "message":"Could not find submission"
            }
            
        return Response(response)

class CompanySubmissionAcceptAPIView(APIView):
    def get(self,request,pk):
        if not submission.objects.filter(program__company=user,id=pk).exists():
            response={
                "message":"Could not find submission"
            }
            return Response(response)

        data=submission.objects.get(program__company=user,id=pk)
        submission_id=pk
        sender_id=user.id
        receiver_id=data.user.id
        message="Your submission accepted"
        try:
            submission.objects.filter(program__company=user.id,id=pk).update(status="accepted")
            message_data=messages.objects.create(submission_id=submission_id,sender_id=sender_id,receiver_id=receiver_id,text=message)
            response={
                "message":"Submission Acceped",
                "message_data":message_data.id
            }
        except:
            response={
                "message":"Could not find submission"
            }
        return Response(response)
        
class CompanyLeaderBoardAPIView(APIView):
    def get(self,request):
        data = professional.objects.filter(reward__gte=1).order_by('-reward')
        data1 = Student.objects.filter(reward__gte=1).order_by('-reward')
       
        response={
            "data":{
            "professional_obj":CompanyProfessionalLeaderBoardSerializer(data,many=True).data,
            "student_obj":CompanyStudentLeaderBoardSerializer(data1,many=True).data
        }

        }
        return Response(response)

class CompanyLeaderBoardDetailAPIView(APIView):
    def get(self,request,pk):
        if Student.objects.filter(student_user__id=pk).exists():
            data=Student.objects.get(student_user__id=pk)
            message="success"
            serializer=CompanyStudentLeaderBoardSerializer(data).data
        elif professional.objects.filter(professional_user__id=pk).exists():
            data=professional.objects.get(professional_user__id=pk)
            message="success"
            serializer=CompanyProfessionalLeaderBoardSerializer(data).data
        else:
            message="failed"
            serializer=None

        response={
            "message":message,
            "data":{
                "leaderdata":serializer
            }
        }
        return Response(response)

class CompanySettingsChangeNameAPIView(APIView):
    def post(self,request,format=None):
        serializer=CompanyChangeNameSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                first_name=request.data['first_name']
                last_name=request.data['last_name']
                profile_description=request.data['description']
                if not first_name.isalpha() or not last_name.isalpha():
                    message="first name or last name is invalid , only alphabet"
                    return Response({"message":message})
                User.objects.filter(id=user.id).update(first_name=first_name,last_name=last_name)
                company.objects.filter(company_user = user).update(description=profile_description)
                message='Successfully updated !'
            except Exception as e:
                message="Failed"
                print(e)
        else:
            message="Retry once again"

        response={
            "message":message
        }
        return Response(response)

class CompanySettingschangeUserNameAPIView(APIView):
    def post(self,request,format=None):
        serializer=CompanyChangeUserNameSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            print('if')
        else:
            print('else')
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

                user = authenticate(
                    request, username=user.username, password=password)
                if user is not None:
                    if user.username != username:
                        if User.objects.filter(username=username).exists():
                            message='Username already taken'
                         
                        else:
                            User.objects.filter(id=user.id).update(username=username)
                            message=' Username successfully updated !'

                    if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
                        print("reached in email2")
                        message='Email already taken'
                    else:
                        token = str(uuid.uuid4())

                        try:
                            ExtendUser_obj= ExtendUser.objects.get(user=user.id)
                            if user.email != email!=ExtendUser_obj.optional_email:
                                ExtendUser.objects.filter(user=request.user.id).update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                send_email_verification_mail(email,token)
                                message='Email successfully updated, Now Verify the email'

                            else:
                                message='You already added this Email'
                            
                        except:
                            ExtendUser.objects.create(user=user,optional_email=email,optional_email_token=token)
                            send_email_verification_mail(email,token)
                            message='Email successfully Added, Now Verify the email '
                            pass
                
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

class CompanySettingsUploadImageAPIView(APIView):
    def post(self,request,format=None):
        data = company.objects.get(company_user=request.user.id)
        serailzer= ComapnyImageUploadSerializer(data=request.data,)
        if not request.FILES:
            message="Image is empty"
        if serailzer.is_valid():
            data = company.objects.get(company_user=request.user.id)
            if data.profile_picture == 'Null':
                serailzer.save()

            else:
                file_exists=os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
            
                serailzer.save()
            message="Profile picture successfully updated !"

        else:
            message="Please select a valid image file"
        response={
            "message":message
        }
        return Response(response)

class CompanySettingsUpdatePasswordAPIView(APIView):
    def post(self,request,format=None):
        serializer=CompanyUpdatePasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            password_1=request.data['password1']
            password_2=request.data['password2']
            password_3=request.data['password3']
            if not password_1 or not password_2 or not password_3:
                message="Fields should not be empty"
            user_obj = authenticate(request, username=user.username, password=password_1) 
            if user_obj is not None:
                if not password_2 and not password_3:
                    message="New password confirm password should not be empty and length more than 9"
                if password_2==password_3:
                    print("reached")
                    password=make_password(password_2)
                    User.objects.filter(id=user.id).update(password=password)
                    user_obj =authenticate(username=user.username, password=password)
                    login(request,user_obj)
                    message="New password updated successfully"
                else:
                    message="New password and confirm password not match"
            else:
                message="Old password not match"

            print('if')
        else:
            message="failed"
            print('else')
        
        response={
            "data":None,
            "message":message
        }
        return Response(response)



class  ComapnySettingsOptionalEmailAPIView(APIView):
    def post(self,request,format=None):
        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
        print(ExtendUser_obj.optional_email_token)
        token=request.data('token')
        if ExtendUser_obj.optional_email_token == token:
            message="email successfully verified"
            ExtendUser.objects.filter(user=request.user.id).update(optional_email_status=True)
        else:
            message="Enter the right token"

        response={
            "message":message
        }
        return Response(response)



class CompanySettingsPhoneValidateAPIView(APIView):
    def post(self,request,format=None):
        print("reached1")
        country=request.data('country')
        phone_number=request.data('phone_number')
        code=request.data('code')
        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
        if code :
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
                if code == ValidateNumber_obj.code:
                    ValidateNumber.objects.filter(user=ExtendUser_obj.id).update(status=True)
                    message="Your phone number successfully validated"
                else:
                    message="Security code doesnot match"
            except:
                pass

        else:
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)

            except:
                ValidateNumber_obj="NULL"
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
                        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
                        ValidateNumber.objects.create(user=ExtendUser_obj,message_id=message_obj.sid,phone_number=number,code=validation_code)
                        message="Security code send to given number"
                except:
                    message="Something went Wrong retry again"
        response={
            "message":message
        }
        return Response(response)

class CompanySettingsAPIView(APIView):
    def get(self,request):
        try:
            program_count=submission.objects.filter(program__company=user.id).count()
            company_obj=company.objects.get(company_user=user.id)
            total_payment=payments.objects.filter(transfer_from = company_obj.id).aggregate(Sum('amount'))
            company_login_details_obj=company_login_details.objects.get(company=company_obj)
            try:
                ExtendUser_obj=ExtendUser.objects.get(user=user.id)
            
            except:
                ExtendUser.objects.create(user=user)
                ExtendUser_obj=ExtendUser.objects.get(user=user.id)
                
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
                "company_obj":CompanySettingsSerializer(company_obj).data,
                "program_count":program_count,
                "total_payment":total_payment,
                "company_login_details_obj":CompanyLoginDetailsSerializer(company_login_details_obj).data,
                "ExtendUser_obj":CompanyExtendedUserSerializer(ExtendUser_obj).data,
                "ValidateNumber_obj":ValidateNumber_obj,}
            

                }
        except Exception as e:
            response={
                "message":"failed",
                "data":None
            }
            print(e)
        return Response(response)

class CompanyLogout(APIView):
    def get(self,request):
        try:
            logout(request)
            message="Successfully Logout"
        except Exception as e:
            message="somthing went wrong"

        response={
            "message":message
        }
        return Response(response)
               