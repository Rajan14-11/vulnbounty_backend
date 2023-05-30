from django.core.mail import send_mail
from django.conf import settings


def send_forget_password_mail(email,token,request):
    host = request.get_host()
    try:
        subject = 'your forget password link'
        message = f'Hi , click on the link to reset your password {host}/change_password/{token}/'
        email_from = settings.EMAIL_HOST_USER
        recipient_list=[email]
        send_mail(subject , message, email_from , recipient_list)
        return True
    except Exception as e:
        return False

def send_email_verification_mail(email,token,request):
   
    try:
        print(email)
        host = request.get_host()
        subject = 'Email verification'
        message = f'Hi , this is your verification token {host}/api/email_verification/{token}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list=[email]
        send_mail(subject , message, email_from , recipient_list)
        return True
    except Exception as e:
        print(e)
        return False


def send_optional_email_verification_mail(request,email,token):
   
    try:
        host = request.get_host()
        subject = 'Email verification'
        message = f'Hi , this is your verification token {host}/api/optional_email_verification/{token}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list=[email]
        send_mail(subject , message, email_from , recipient_list)
        return True
    except Exception as e:
        print(e)
        return False

def error_handle(error):

    error_message=[]
    for field_name, field_errors in error.items():
        print(field_errors[0])
        error_message.append(field_errors[0])
    print("error",error)
    return error_message