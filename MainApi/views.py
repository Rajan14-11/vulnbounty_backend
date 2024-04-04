from rest_framework.views import APIView
from django.conf import settings
from rest_framework.response import Response
import socket
from .serializers import LoginSerializer, ValidatePhoneSerializer, PhoneValidation, ForgotPasswordSerializer, ChangePasswordSerializer
from django.contrib.auth import authenticate, login, logout
from StudentApi.models import Student, student_login_details
from CompanyApi.models import company, company_login_details
from ProfessionalApi.models import professional, professional_login_details
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ExtendUser, ValidateNumber,UserToken
from twilio.rest import Client
from .renderers import UserRender
import uuid
from .helpers import send_forget_password_mail, send_email_verification_mail, error_handle
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from datetime import timedelta, datetime
import random
import string
import socket
import jwt
from rest_framework import status
import secrets
# import datetime


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

# class LoginAPIView(APIView):
#     renderer_classes=[UserRender]
#     def post(self,request,format=None):
#         # User.objects.all().delete()
#         role=""

#         h_name = socket.gethostname()
#         IP_addres = socket.gethostbyname(h_name)
#         serializer =LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             print("error",serializer.errors)
#             print("reached in valid")
#             username = serializer.data['username']
#             password = serializer.data['password']
#             print(username,password)
#             token=None
#             user =authenticate(username=username, password=password)
#             if user is not None:
#                 token=get_tokens_for_user(user)
#                 if Student.objects.filter(student_user=user.id).exists():
#                     role="student_dashboard"
#                     message="success"
#                     student_obj=Student.objects.get(student_user=user.id)
#                     login(request, user)
#                     if student_login_details.objects.filter(student=student_obj).exists():
#                         student_login_details_obj=student_login_details.objects.get(student=student_obj.id)
#                         student_login_details.objects.filter(student=student_obj.id).update(ip_address=IP_addres,old_ip_address=student_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=student_login_details_obj.new_login_time,host_name=h_name,old_host_name=student_login_details_obj.host_name)

#                     else:
#                         student_login_details.objects.create(
#                             student=student_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now(),
#                         )

#                 elif professional.objects.filter(professional_user=user.id).exists():
#                     role="professional_dashboard"
#                     message="success"
#                     professional_obj=professional.objects.get(professional_user=user.id)
#                     login(request, user)
#                     if professional_login_details.objects.filter(professional=professional_obj.id).exists():
#                         professional_login_details_obj=professional_login_details.objects.get(professional=professional_obj)
#                         professional_login_details.objects.filter(professional=professional_obj).update(ip_address=IP_addres,old_ip_address=professional_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=professional_login_details_obj.new_login_time,host_name=h_name,old_host_name=professional_login_details_obj.host_name)

#                     else:
#                         professional_login_details.objects.create(professional=professional_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())
#                 elif company.objects.filter(company_user=user.id).exists():
#                     role="company_dashboard"
#                     message="success"
#                     company_obj=company.objects.get(company_user=user.id)
#                     login(request, user)
#                     if company_login_details.objects.filter(company=company_obj.id).exists():
#                         company_login_details_obj=company_login_details.objects.get(company=company_obj)
#                         company_login_details.objects.filter(company=company_obj).update(ip_address=IP_addres,old_ip_address=company_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=company_login_details_obj.new_login_time,host_name=h_name,old_host_name=company_login_details_obj.host_name)

#                         print(user.id)
#                     else:
#                         company_login_details.objects.create(company=company_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())

#                 else:
#                     message="No User found"
#             response={
#             "token":token,
#             "message":message,
#             "role":role
#                 }
#             return Response(response)
#         else:
#             # default_errors=serializer.errors
#             message=error_handle(serializer.errors)
#             print("message",message)


#             return Response(message)

#             # field_names = []
#             # error_message=[]
#             # for field_name, field_errors in default_errors.items():
#             #     field_names.append(field_name)
#             # for errors in default_errors.items():

#             #     error_message.append((errors[1]))
#             # print("error_message",error_message)
#             # print("errors",default_errors.items())
#             # return Response({'error': f'{field_names} is required'})


#             message="Try Again Later"
#             response={
#             "message":message,
#                 }
#             return Response(response)


#         # try:
#         #     client_key=request.POST.get('g-recaptcha-response')
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

#  # verify=True
#         # if verify == True:

#         # else:
#         #     message="reCAPTCHA not verifyied"

#         # response={
#         #     "token":token,
#         #     "message":message
#         # }

# class LoginAPIView(APIView):
#     renderer_classes = [UserRender]

#     def post(self, request, format=None):
#         h_name = socket.gethostname()
#         IP_addres = socket.gethostbyname(h_name)
#         serializer = LoginSerializer(data=request.data)


#         if serializer.is_valid():
#             username = serializer.data['username']
#             password = serializer.data['password']

#             token = None
#             user = authenticate(username=username, password=password)
#             passwordhash = make_password(password)
#             print(passwordhash)

#             if user is not None:
#                 token = get_tokens_for_user(user)
#                 role = ""
#                 message = "success"
#                 question_completed= False

#                 if company.objects.filter(company_user=user.id).exists():
#                     role = "company_dashboard"
#                     company_obj = company.objects.get(company_user=user.id)
#                     login(request, user)

#                     if company_login_details.objects.filter(company=company_obj.id).exists():
#                         company_login_details_obj = company_login_details.objects.get(company=company_obj)
#                         company_login_details.objects.filter(company=company_obj).update(
#                             ip_address=IP_addres,
#                             old_ip_address=company_login_details_obj.ip_address,
#                             new_login_time=datetime.datetime.now(),
#                             old_login_time=company_login_details_obj.new_login_time,
#                             host_name=h_name,
#                             old_host_name=company_login_details_obj.host_name
#                         )
#                     else:
#                         company_login_details.objects.create(
#                             company=company_obj,
#                             ip_address=IP_addres,
#                             old_ip_address=IP_addres,
#                             host_name=h_name,
#                             old_host_name=h_name,
#                             old_login_time=datetime.datetime.now()
#                         )

#                 elif professional.objects.filter(professional_user=user.id).exists():
#                     role = "professional_dashboard"
#                     professional_obj = professional.objects.get(professional_user=user.id)
#                     question_completed = professional_obj.questions_completed
#                     login(request, user)

#                     if professional_login_details.objects.filter(professional=professional_obj.id).exists():
#                         professional_login_details_obj = professional_login_details.objects.get(professional=professional_obj)
#                         professional_login_details.objects.filter(professional=professional_obj).update(
#                             ip_address=IP_addres,
#                             old_ip_address=professional_login_details_obj.ip_address,
#                             new_login_time=datetime.datetime.now(),
#                             old_login_time=professional_login_details_obj.new_login_time,
#                             host_name=h_name,
#                             old_host_name=professional_login_details_obj.host_name
#                         )
#                     else:
#                         professional_login_details.objects.create(
#                             professional=professional_obj,
#                             ip_address=IP_addres,
#                             old_ip_address=IP_addres,
#                             host_name=h_name,
#                             old_host_name=h_name,
#                             old_login_time=datetime.datetime.now()
#                         )


#                         if not professional_obj.quiz_completed:
#                             professional.objects.filter(professional_user=user.id).update(quiz_completed=True)
#                             message = "success (Quiz completed for professional)"

#                 elif Student.objects.filter(student_user=user.id).exists():
#                     role = "student_dashboard"
#                     student_obj = Student.objects.get(student_user=user.id)
#                     login(request, user)

#                     if student_login_details.objects.filter(student=student_obj).exists():
#                         student_login_details_obj = student_login_details.objects.get(student=student_obj.id)
#                         student_login_details.objects.filter(student=student_obj.id).update(
#                             ip_address=IP_addres,
#                             old_ip_address=student_login_details_obj.ip_address,
#                             new_login_time=datetime.datetime.now(),
#                             old_login_time=student_login_details_obj.new_login_time,
#                             host_name=h_name,
#                             old_host_name=student_login_details_obj.host_name
#                         )
#                     else:
#                         student_login_details.objects.create(
#                             student=student_obj,
#                             ip_address=IP_addres,
#                             old_ip_address=IP_addres,
#                             host_name=h_name,
#                             old_host_name=h_name,
#                             old_login_time=datetime.datetime.now(),
#                         )

#                 else:
#                     message = "No User found"

#             response = {
#                 "token": token,
#                 "message": message,
#                 "role": role,
#                 "questions_completed":question_completed
#             }
#             return Response(response)
#         else:
#             message = error_handle(serializer.errors)
#             return Response(message)

class LoginAPIView(APIView):
    renderer_classes = [UserRender]

    def post(self, request, format=None):
        role = ""
        h_name = socket.gethostname()
        IP_address = socket.gethostbyname(h_name)
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data['username']
            password = serializer.data['password']
            remember_me = serializer.data.get('remember_me', False)

            token = None
            user = authenticate(username=username, password=password)
            if user is not None:
                question_completed = False
                token_expiration = timedelta(
                    minutes=6000) if not remember_me else timedelta(days=7)
                settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = token_expiration
                settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = token_expiration
                token = RefreshToken.for_user(user)

                # Save token in the database
                self.save_token_in_database(user, token)

                if Student.objects.filter(student_user=user.id).exists():
                    role = "student_dashboard"
                    message = "success"
                    student_obj = Student.objects.get(student_user=user.id)
                    login(request, user)
                    # Update login details
                    if student_login_details.objects.filter(student=student_obj).exists():
                        student_login_details_obj = student_login_details.objects.get(
                            student=student_obj.id)
                        student_login_details.objects.filter(student=student_obj.id).update(
                            ip_address=IP_address,
                            old_ip_address=student_login_details_obj.ip_address,
                            new_login_time=datetime.now(),
                            old_login_time=student_login_details_obj.new_login_time,
                            host_name=h_name,
                            old_host_name=student_login_details_obj.host_name
                        )
                    else:
                        student_login_details.objects.create(
                            student=student_obj,
                            ip_address=IP_address,
                            old_ip_address=IP_address,
                            host_name=h_name,
                            old_host_name=h_name,
                            old_login_time=datetime.now(),
                        )
                elif professional.objects.filter(professional_user=user.id).exists():
                    role = "professional_dashboard"
                    message = "success"
                    professional_obj = professional.objects.get(
                        professional_user=user.id)
                    question_completed = professional_obj.questions_completed
                    login(request, user)
                    if professional_login_details.objects.filter(professional=professional_obj.id).exists():
                        professional_login_details_obj = professional_login_details.objects.get(
                            professional=professional_obj)
                        professional_login_details.objects.filter(professional=professional_obj).update(
                            ip_address=IP_address,
                            old_ip_address=professional_login_details_obj.ip_address,
                            new_login_time=datetime.now(),
                            old_login_time=professional_login_details_obj.new_login_time,
                            host_name=h_name,
                            old_host_name=professional_login_details_obj.host_name
                        )
                    else:
                        professional_login_details.objects.create(
                            professional=professional_obj,
                            ip_address=IP_address,
                            old_ip_address=IP_address,
                            host_name=h_name,
                            old_host_name=h_name,
                            old_login_time=datetime.now()
                        )
                elif company.objects.filter(company_user=user.id).exists():
                    role = "company_dashboard"
                    message = "success"
                    company_obj = company.objects.get(company_user=user.id)
                    login(request, user)
                    if company_login_details.objects.filter(company=company_obj.id).exists():
                        company_login_details_obj = company_login_details.objects.get(
                            company=company_obj)
                        company_login_details.objects.filter(company=company_obj).update(
                            ip_address=IP_address,
                            old_ip_address=company_login_details_obj.ip_address,
                            new_login_time=datetime.now(),
                            old_login_time=company_login_details_obj.new_login_time,
                            host_name=h_name,
                            old_host_name=company_login_details_obj.host_name
                        )
                    else:
                        company_login_details.objects.create(
                            company=company_obj,
                            ip_address=IP_address,
                            old_ip_address=IP_address,
                            host_name=h_name,
                            old_host_name=h_name,
                            old_login_time=datetime.now()
                        )
                else:
                    message = "No User found"

                # Construct the response with nested tokens
                response = {
                    "token": {
                        "refresh": str(token),
                        "access": str(token.access_token)
                    },
                    "message": message,
                    "questions_completed": question_completed,
                    "role": role
                }
                return Response(response)
            else:
                message = "No User found"
        else:
            message = error_handle(serializer.errors)
            print("message", message)

        return Response(message)

    def save_token_in_database(self, user, token):
        # Save the token in the database associated with the user
        # You need to adjust this code based on your database structure
        user_token, created = UserToken.objects.get_or_create(user=user)
        user_token.access_token = str(token.access_token)
        user_token.refresh_token = str(token)
        user_token.save()



class ConfirmEmailAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self, request, token):
        try:
            if Student.objects.filter(email_verification_token=token).exists():
                Student.objects.filter(
                    email_verification_token=token).update(email_status=True)
                message="Your email have verified successfully, now login"
                user_type="student"
            elif professional.objects.filter(email_verification_token=token).exists():
                professional.objects.filter(
                    email_verification_token=token).update(email_status=True)
                message="Your email have verified successfully, now login"
                user_type="professional"
            elif company.objects.filter(email_verification_token=token).exists():
                company.objects.filter(
                    email_verification_token=token).update(email_status=True)
                message="Your email have verified successfully, now login"
                user_type="company"

            else:
                message="your email not verified"
                user_type=None

        except Exception as e:
           message="error"
           user_type=None
        response={
            "message": message,
            "user_type": user_type
        }

        return Response(response)


class OptionalEmailAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self, request, token):
        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
        if ExtendUser_obj.optional_email_token == token:
            message="email successfully verified"
            ExtendUser.objects.filter(user=request.user.id).update(
                optional_email_status=True)
        else:
            message="Enter the right token"

        response={
            "message": message
        }
        return Response(response)


class PhoneValidateAPIView(APIView):
    renderer_classes=[UserRender]
    def get(self, request):
        try:
            ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
            ValidateNumber_obj=ValidateNumber.objects.get(
                user=ExtendUser_obj.id)
            response={
                "message": "success",
                "data": {
                    "phone_validation": PhoneValidation(ValidateNumber_obj).data,
                }
            }
        except:
             response={
                "message": "failed",
                "data": None
            }

        return Response(response)


    def post(self, request, format=None):
        serializer=ValidatePhoneSerializer(data=request.data)
        message=""
        if serializer.is_valid():
            country=request.data['country_code']
            phone_number=request.data['phone_number']
            code=request.data['code']
            # try:

            # except:
            #     code=None
            ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
            if type(code) == int:
                try:
                    ValidateNumber_obj=ValidateNumber.objects.get(
                        user=ExtendUser_obj.id)
                    if code == ValidateNumber_obj.code:
                        ValidateNumber.objects.filter(
                            user=ExtendUser_obj.id).update(status=True)
                        message="Your phone number successfully validated"
                    else:
                        message="Security code doesnot match"
                except:
                    message="Something went Wrong retry again"
                    pass

            else:
                try:
                    ValidateNumber_obj=ValidateNumber.objects.get(
                        user=ExtendUser_obj.id)

                except:
                    ValidateNumber_obj="NULL"
                    number=f'{country}{phone_number}'
                    account_sid=settings.TWILIO_ACCOUNT_SID
                    auth_token=settings.TWILIO_AUTH_TOKEN
                    client=Client(account_sid, auth_token)
                    validation_code=9023456
                    try:
                            message_obj=client.messages.create(
                                                    body=f'Your Vulnbounty security code {validation_code}',
                                                    from_='+13465123951',
                                                    to=number
                                                )
                            ExtendUser_obj=ExtendUser.objects.get(
                                user=request.user.id)
                            ValidateNumber.objects.create(
                                user=ExtendUser_obj, message_id=message_obj.sid, phone_number=number, code=validation_code)
                            message="Security code send to given number"
                    except Exception as e:
                        print(e)
                        message="Something went Wrong retry again"
        else:
             message=error_handle(serializer.errors)
        return Response(message)


class ForgotPasswordAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self, request):
        serializer=ForgotPasswordSerializer(data=request.data)
        message=""
        if serializer.is_valid():
            email=request.data['email']
            if not User.objects.filter(email=email).first():
                message="A new password has been sent to your email. Kindly check your mail."
            user_obj=User.objects.get(email=email)
            token=str(uuid.uuid4())
            if Student.objects.filter(student_user=user_obj.id).exists():
                student_data=Student.objects.get(student_user=user_obj.id)
                student_data.forget_password_token=token
                student_data.save()
                random_password=''.join(random.choices(
                    string.ascii_letters + string.digits, k=12))
                user_obj.set_password(random_password)
                user_obj.save()
                send_forget_password_mail(
                    user_obj.email, random_password, request)
                message="A new password has been sent to your email. Kindly check your mail."
            if professional.objects.filter(professional_user=user_obj.id).exists():
                professional_data=professional.objects.get(
                    professional_user=user_obj.id)
                professional_data.forget_password_token=token
                professional_data.save()
                random_password=secrets.token_urlsafe(6)
                # random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                password=make_password(random_password)
                print(password)
                User.objects.filter(id=user_obj.id).update(password=password)
                # user_obj.save()
                send_forget_password_mail(
                    user_obj.email, random_password, request)
                message="A new password has been sent to your email. Kindly check your mail."
            if company.objects.filter(company_user=user_obj.id).exists():
                company_data=company.objects.get(company_user=user_obj.id)
                company_data.forget_password_token=token
                company_data.save()
                random_password=''.join(random.choices(
                    string.ascii_letters + string.digits, k=12))
                password=make_password(random_password)
                print(password)
                User.objects.filter(id=user_obj.id).update(password=password)
                # user_obj.set_password(password)
                # user_obj.save()
                send_forget_password_mail(
                    user_obj.email, random_password, request)
                message="A new password has been sent to your email. Kindly check your mail."
            response={
            "message": message
        }
            return Response(response)
        else:
            message=error_handle(serializer.errors)
            return Response(message)

class ChangePasswordAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self, request):
        serializer=ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            token=request.data['token']
            if Student.objects.filter(forget_password_token=token).exists():
                student_obj=Student.objects.filter(
                    forget_password_token=token).first()
                user_id=student_obj.student_user.id
            if professional.objects.filter(forget_password_token=token).exists():
                professional_obj=professional.objects.filter(
                    forget_password_token=token).first()
                user_id=professional_obj.professional_user.id
            if company.objects.filter(forget_password_token=token).exists():
                company_obj=company.objects.filter(
                    forget_password_token=token).first()
                user_id=company_obj.company_user.id
            password_1=request.data['password']
            password_2=request.data['confirm_password']
            if password_1 == password_2:
                password=make_password(password_2)
                User.objects.filter(id=user_id).update(password=password)
                message="New password updated successfully"
            else:
                message="New password and confirm password not match"
            response={
            "message": message
        }
            return Response(response)
        else:
            message=error_handle(serializer.errors)
            return Response(message)




class EmailVerificationAPIView(APIView):
    renderer_classes=[UserRender]
    def post(self, request):
        serializer=ForgotPasswordSerializer(data=request.data)
        message=""
        if serializer.is_valid():
            email=request.data['email']
            if not User.objects.filter(email=email).first():
                message="you will get email verification if you registered with this username "
            user_obj=User.objects.get(email=email)
            token=str(uuid.uuid4())
            if Student.objects.filter(student_user=user_obj.id).exists():
                student_data=Student.objects.get(student_user=user_obj.id)
                student_data.email_verification_token=token
                student_data.save()
                send_email_verification_mail(user_obj.email, token, request)
                message="you will get email verification if you registered with this username "

            if professional.objects.filter(professional_user=user_obj.id).exists():
                professional_data=professional.objects.get(
                    professional_user=user_obj.id)
                professional_data.email_verification_token=token
                professional_data.save()
                send_email_verification_mail(user_obj.email, token, request)
                message="you will get email verification if you registered with this username "

            if company.objects.filter(company_user=user_obj.id).exists():
                company_data=company.objects.get(company_user=user_obj.id)
                company_data.email_verification_token=token
                company_data.save()
                send_email_verification_mail(user_obj.email, token, request)
                message="you will get email verification if you registered with this username "

            response={
            "message": message
        }
            return Response(response)
        else:
            message=error_handle(serializer.errors)
            return Response(message)


class Logout(APIView):
    def get(self, request):
        try:
            logout(request)
            message="Successfully Logout"
        except Exception as e:
            message="somthing went wrong"

        response={
            "message": message
        }
        return Response(response)


class ActivateAccountAPIView(APIView):

    def post(self, request):
        user=request.user

        # Assuming the request contains the email of the account to be activated
        user_email=request.data.get('email')

        if not user_email:
            return Response({'error': 'Email not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Try to find the user by email
            user_to_activate=User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the requesting user has permission to activate the account
        # if not user.is_staff:
        #     return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the account is already active
        if user_to_activate.is_active:
            return Response({'message': 'Account is already active'}, status=status.HTTP_400_BAD_REQUEST)

        # Activate the account
        user_to_activate.is_active=True
        user_to_activate.save()

        response_data={
            'message': 'Account activated successfully',
            'user_id': user_to_activate.id,
            'username': user_to_activate.username,
            'email': user_to_activate.email,
        }

        return Response(response_data, status=status.HTTP_200_OK)
