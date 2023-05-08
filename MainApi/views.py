from rest_framework.views import APIView
from django.conf import settings
from rest_framework.response import Response
import socket
from .serializers import LoginSerializer,ValidatePhoneSerializer,PhoneValidation,ForgotPasswordSerializer,ChangePasswordSerializer
from django.contrib.auth import authenticate, login, logout
from StudentApi.models import Student,student_login_details
from CompanyApi.models import company,company_login_details
from ProfessionalApi.models import professional,professional_login_details
import datetime
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ExtendUser,ValidateNumber
from twilio.rest import Client
from .renderers import UserRender
import uuid
from .helpers import send_forget_password_mail,send_email_verification_mail
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
# Create your views here.
# class RegisterAPI(APIView):
#     def get(self,request,format=None):
#         print("reached")
#         return Response({"data":"this is a data"})

#     def post(self,request,format=None):
#         print(request.data)

#         data=request.data
#         # client_key=request.POST.get('g-recaptcha-response')
#         # secret_key=settings.RECAPTCHA_SECRET_KEY
#         # captcha_data={
#         #         "secret":secret_key,
#         #         "response":client_key
#         #     }
#         # response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
#         # response=json.loads(response_data.text)
#         # verify=response['success']
#         # print(f'verify is = {verify}')
#         # if verify == True:
#         #     terms_and_policy=request.POST.get('terms_and_policy')
#         #     if not terms_and_policy == 'checked':
#         #         message="please tick the privacy policy and terms"
#         #         return redirect('student_register')
#         #     form = registeration_form(request.POST)
#         #     if form.is_valid():
#         #         password=form.cleaned_data.get('password')
#         #         confirm_password=form.cleaned_data.get('confirm_password')
#         #         print(password,confirm_password)
#         #         if password != confirm_password:
#         #             message.warning(request,"password and confirm pasword didn't match")
#         #             context={'form':form,'values':values}
#         #             return render(request,"Main/student_register.html",context)
#         #         token = str(uuid.uuid4())
#         #         user=form.save(commit=False)
#         #         user.password=make_password(request.POST['password'])
#         #         user.username=form.cleaned_data['username']
#         #         user.save()
#         #         Student_creation = Student.objects.create(student_user=user,email_verification_token =  token,terms_and_policy=True)
#         #         if Student_creation:
#         #             send_email_verification_mail(request,user.email,token)
#         #             student_wallet.objects.create(student=Student_creation)
#         #             message.success(request,'Account created Successfully ! verify your email')
#         #             return redirect('login')
#         #         else:
#         #             message.success(request,'Account not created , Retry please')
#         #             return redirect('student_register')

#         # else:
#         #     message.success(request,'reCAPTCHA not verifyied')
#         #     return redirect('student_register')
#         return Response(data)
       
class LoginAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self,request,format=None):
        # User.objects.all().delete()
        role=""

        h_name = socket.gethostname()
        IP_addres = socket.gethostbyname(h_name)
        serializer =LoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            print("reached in valid")
            username = serializer.data['username']
            password = serializer.data['password']
            print(username,password)
            token=None
            user =authenticate(username=username, password=password)
            if user is not None:
                token=get_tokens_for_user(user)
                if Student.objects.filter(student_user=user.id).exists():
                    role="student_dashboard"
                    message="success"
                    student_obj=Student.objects.get(student_user=user.id)
                    login(request, user)
                    if student_login_details.objects.filter(student=student_obj).exists():
                        student_login_details_obj=student_login_details.objects.get(student=student_obj.id)
                        student_login_details.objects.filter(student=student_obj.id).update(ip_address=IP_addres,old_ip_address=student_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=student_login_details_obj.new_login_time,host_name=h_name,old_host_name=student_login_details_obj.host_name)

                    else:
                        student_login_details.objects.create(
                            student=student_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now(),
                        )
                       
                elif professional.objects.filter(professional_user=user.id).exists():
                    role="professional_dashboard"
                    message="success"
                    professional_obj=professional.objects.get(professional_user=user.id)
                    login(request, user)
                    if professional_login_details.objects.filter(professional=professional_obj.id).exists():
                        professional_login_details_obj=professional_login_details.objects.get(professional=professional_obj)
                        professional_login_details.objects.filter(professional=professional_obj).update(ip_address=IP_addres,old_ip_address=professional_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=professional_login_details_obj.new_login_time,host_name=h_name,old_host_name=professional_login_details_obj.host_name)
                        
                    else:
                        professional_login_details.objects.create(professional=professional_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())
                elif company.objects.filter(company_user=user.id).exists():
                    role="company_dashboard"
                    message="success"
                    company_obj=company.objects.get(company_user=user.id)
                    login(request, user)
                    if company_login_details.objects.filter(company=company_obj.id).exists():
                        company_login_details_obj=company_login_details.objects.get(company=company_obj)
                        company_login_details.objects.filter(company=company_obj).update(ip_address=IP_addres,old_ip_address=company_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=company_login_details_obj.new_login_time,host_name=h_name,old_host_name=company_login_details_obj.host_name)
                        
                        print(user.id)
                    else:
                        company_login_details.objects.create(company=company_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())
                        
                else:
                    message="No User found"
        else:
            message="Try Again Later"
          
        response={
            "token":token,
            "message":message,
            "role":role
                }
        return Response(response)

        # try:
        #     client_key=request.POST.get('g-recaptcha-response')
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
       
 # verify=True
        # if verify == True:
        
        # else:
        #     message="reCAPTCHA not verifyied"
        
        # response={
        #     "token":token,
        #     "message":message
        # }

       

class ConfirmEmailAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self,request,token):
        try:
            if Student.objects.filter(email_verification_token =token).exists():
                Student.objects.filter(email_verification_token =token).update(email_status=True)
                message="Your email have verified successfully, now login" 
                user_type="student"   
            elif professional.objects.filter(email_verification_token =token).exists():
                professional.objects.filter(email_verification_token =token).update(email_status=True)
                message="Your email have verified successfully, now login" 
                user_type="professional"   
            elif company.objects.filter(email_verification_token =token).exists():
                company.objects.filter(email_verification_token =token).update(email_status=True)
                message="Your email have verified successfully, now login" 
                user_type="company" 
                
            else:
                message="your email not verified"
                user_type=None

        except Exception as e :
           message="error"
           user_type=None
        response={
            "message":message,
            "user_type":user_type
        }

        return Response(response)


class  OptionalEmailAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self,request,token):
        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
        if ExtendUser_obj.optional_email_token == token:
            message="email successfully verified"
            ExtendUser.objects.filter(user=request.user.id).update(optional_email_status=True)
        else:
            message="Enter the right token"

        response={
            "message":message
        }
        return Response(response)


class PhoneValidateAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self,request):
        try:
            ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
            ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
            response={
                "message":"success",
                "data":{
                    "phone_validation":PhoneValidation(ValidateNumber_obj).data,
                }
            }
        except:
             response={
                "message":"failed",
                "data":None
            }

        return Response(response)


    def post(self,request,format=None):
        serializer=ValidatePhoneSerializer(data=request.data)
        message=""
        if serializer.is_valid(raise_exception=True):
            country=request.data['country_code']
            phone_number=request.data['phone_number']
            code=request.data['code']
            # try:
                
            # except:
            #     code=None
            ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
            if type(code) == int :
                try:
                    ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
                    if code == ValidateNumber_obj.code:
                        ValidateNumber.objects.filter(user=ExtendUser_obj.id).update(status=True)
                        message="Your phone number successfully validated"
                    else:
                        message="Security code doesnot match"
                except:
                    message="Something went Wrong retry again"
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
                                                    from_='+13465123951',
                                                    to=number
                                                )
                            ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
                            ValidateNumber.objects.create(user=ExtendUser_obj,message_id=message_obj.sid,phone_number=number,code=validation_code)
                            message="Security code send to given number"
                    except Exception as e:
                        print(e)
                        message="Something went Wrong retry again"
            response={
                "message":message
            }
        else:
             response={
                "message":message
            }
        return Response(response)

class ForgotPasswordAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self,request):
        serializer=ForgotPasswordSerializer(data=request.data)
        message=""
        if serializer.is_valid(raise_exception=True):
            username=request.data['username']
            print(username)
            if not User.objects.filter(username = username).first():
                message="you will get reset password if you registered with this username"
            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())
            if Student.objects.filter(student_user=user_obj.id).exists():
                student_data=Student.objects.get(student_user=user_obj.id)
                student_data.forget_password_token = token
                student_data.save()
                send_forget_password_mail(user_obj.email,token,request)
                message="you will get reset password if you registered with this username"
            if professional.objects.filter(professional_user=user_obj.id).exists():
                professional_data = professional.objects.get(professional_user = user_obj.id)
                professional_data.forget_password_token = token
                professional_data.save()
                send_forget_password_mail(user_obj.email,token,request)
                message="you will get reset password if you registered with this username"
            if company.objects.filter(company_user=user_obj.id).exists():
                company_data = company.objects.get(company_user = user_obj.id)
                company_data.forget_password_token = token
                company_data.save()
                send_forget_password_mail(user_obj.email,token,request)
                message="you will get reset password if you registered with this username"
                
        response={
            "message":message
        }
        return Response(response)
    
class ChangePasswordAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self,request):
        serializer=ChangePasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            token=request.data['token']
            if Student.objects.filter(forget_password_token=token).exists():
                student_obj =Student.objects.filter(forget_password_token=token).first()
                user_id=student_obj.student_user.id    
            if professional.objects.filter(forget_password_token=token).exists():
                professional_obj = professional.objects.filter(forget_password_token=token).first()
                user_id=professional_obj.professional_user.id
            if company.objects.filter(forget_password_token=token).exists():
                company_obj = company.objects.filter(forget_password_token=token).first()
                user_id=company_obj.company_user.id
            password_1=request.data['password']
            password_2=request.data['confirm_password']
            if password_1==password_2:
                password=make_password(password_2)
                User.objects.filter(id=user_id).update(password=password)
                message="New password updated successfully"
            else:
                message="New password and confirm password not match"
        else:
            message="Retry again"
        response={
            "message":message
        }
        return Response(response)
    

class EmailVerificationAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self,request):
        serializer=ForgotPasswordSerializer(data=request.data)
        message=""
        if serializer.is_valid(raise_exception=True):
            username=request.data['username']
            print(username)
            if not User.objects.filter(username = username).first():
                message="you will get email verification if you registered with this username "
            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())
            if Student.objects.filter(student_user=user_obj.id).exists():
                student_data=Student.objects.get(student_user=user_obj.id)
                student_data.email_verification_token = token
                student_data.save()
                send_email_verification_mail(user_obj.email,token,request)
                message="you will get email verification if you registered with this username "
            if professional.objects.filter(professional_user=user_obj.id).exists():
                professional_data = professional.objects.get(professional_user = user_obj.id)
                professional_data.email_verification_token = token
                professional_data.save()
                send_email_verification_mail(user_obj.email,token,request)
                message="you will get email verification if you registered with this username "
            if company.objects.filter(company_user=user_obj.id).exists():
                company_data = company.objects.get(company_user = user_obj.id)
                company_data.email_verification_token = token
                company_data.save()
                send_email_verification_mail(user_obj.email,token,request)
                message="you will get email verification if you registered with this username "
                
        response={
            "message":message
        }
        return Response(response)
    
class Logout(APIView):
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
    
