from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from django.http import JsonResponse
from django.conf import settings
import requests
import json
from rest_framework.response import Response
import socket
from .serializers import LoginSerializer
from django.contrib.auth import authenticate, login, logout
from StudentApi.models import Student,student_login_details
from CompanyApi.models import company,company_login_details
from ProfessionalApi.models import professional,professional_login_details
import datetime
# Create your views here.
class RegisterAPI(APIView):
    def get(self,request,format=None):
        print("reached")
        return Response({"data":"this is a data"})

    def post(self,request,format=None):
        print(request.data)

        data=request.data
        # client_key=request.POST.get('g-recaptcha-response')
        # secret_key=settings.RECAPTCHA_SECRET_KEY
        # captcha_data={
        #         "secret":secret_key,
        #         "response":client_key
        #     }
        # response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
        # response=json.loads(response_data.text)
        # verify=response['success']
        # print(f'verify is = {verify}')
        # if verify == True:
        #     terms_and_policy=request.POST.get('terms_and_policy')
        #     if not terms_and_policy == 'checked':
        #         message="please tick the privacy policy and terms"
        #         return redirect('student_register')
        #     form = registeration_form(request.POST)
        #     if form.is_valid():
        #         password=form.cleaned_data.get('password')
        #         confirm_password=form.cleaned_data.get('confirm_password')
        #         print(password,confirm_password)
        #         if password != confirm_password:
        #             message.warning(request,"password and confirm pasword didn't match")
        #             context={'form':form,'values':values}
        #             return render(request,"Main/student_register.html",context)
        #         token = str(uuid.uuid4())
        #         user=form.save(commit=False)
        #         user.password=make_password(request.POST['password'])
        #         user.username=form.cleaned_data['username']
        #         user.save()
        #         Student_creation = Student.objects.create(student_user=user,email_verification_token =  token,terms_and_policy=True)
        #         if Student_creation:
        #             send_email_verification_mail(request,user.email,token)
        #             student_wallet.objects.create(student=Student_creation)
        #             message.success(request,'Account created Successfully ! verify your email')
        #             return redirect('login')
        #         else:
        #             message.success(request,'Account not created , Retry please')
        #             return redirect('student_register')

        # else:
        #     message.success(request,'reCAPTCHA not verifyied')
        #     return redirect('student_register')
        return Response(data)
       
class LoginAPIView(APIView):
    def post(self,request,format=None):

        h_name = socket.gethostname()
        IP_addres = socket.gethostbyname(h_name)

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
        verify=True
        if verify == True:
            serializer =LoginSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                username = serializer.data['username']
                password = serializer.data['password']
                print(username,password)
                user =authenticate(username=username, password=password)
                if user is not None:
                    if Student.objects.filter(student_user=user.id).exists():
                        student_obj=Student.objects.get(student_user=user.id)
                        login(request, user)
                        if student_login_details.objects.filter(student=student_obj).exists():
                            student_login_details_obj=student_login_details.objects.get(student=student_obj.id)
                            student_login_details.objects.filter(student=student_obj.id).update(ip_address=IP_addres,old_ip_address=student_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=student_login_details_obj.new_login_time,host_name=h_name,old_host_name=student_login_details_obj.host_name)
                            message="student_dashboard"

                        else:
                            student_login_details.objects.create(
                                student=student_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now(),
                            )
                            message="student_dashboard"
                    elif professional.objects.filter(professional_user=user.id).exists():
                        professional_obj=professional.objects.get(professional_user=user.id)
                        login(request, user)
                        if professional_login_details.objects.filter(professional=professional_obj.id).exists():
                            professional_login_details_obj=professional_login_details.objects.get(professional=professional_obj)
                            professional_login_details.objects.filter(professional=professional_obj).update(ip_address=IP_addres,old_ip_address=professional_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=professional_login_details_obj.new_login_time,host_name=h_name,old_host_name=professional_login_details_obj.host_name)
                            message="professional_dashboard"
                        else:
                            professional_login_details.objects.create(professional=professional_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())
                            message="professional_dashboard"
                    elif company.objects.filter(company_user=user.id).exists():
                        company_obj=company.objects.get(company_user=user.id)
                        login(request, user)
                        if company_login_details.objects.filter(company=company_obj.id).exists():
                            company_login_details_obj=company_login_details.objects.get(company=company_obj)
                            company_login_details.objects.filter(company=company_obj).update(ip_address=IP_addres,old_ip_address=company_login_details_obj.ip_address,new_login_time=datetime.datetime.now(),old_login_time=company_login_details_obj.new_login_time,host_name=h_name,old_host_name=company_login_details_obj.host_name)
                            message="company_dashboard"
                            print(user.id)
                        else:
                            company_login_details.objects.create(company=company_obj,ip_address=IP_addres,old_ip_address=IP_addres,host_name=h_name,old_host_name=h_name,old_login_time=datetime.datetime.now())
                            message="company_dashboard"
                    else:
                        message="login"
                else:
                    message="Username and Password doesn't match"
        else:
            message="reCAPTCHA not verifyied"
        
        response={
            "message":message
        }


        return Response(response)

