
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import validate_image_file_extension
from django.core.validators import FileExtensionValidator

from django.conf import settings
from CompanyApi.models import companyProgram

# Create your models here.
class Student(models.Model):
    student_user = models.ForeignKey(User,on_delete=models.CASCADE)
    phone=models.IntegerField(null = True)
    profile_picture=models.ImageField(null = True,blank = True,upload_to='student/images/profile_picture',default='Null',validators=[validate_image_file_extension])
    resume = models.FileField(null = True,blank = True,upload_to='student/document/resume' ,default='Null',validators=[FileExtensionValidator(['pdf'])])
    profile_description=models.CharField(null = True,max_length=60)
    forget_password_token=models.CharField(max_length=100,null=True)
    email_verification_token =models.CharField(max_length=100,null=True)
    email_status = models.BooleanField(default=False) 
    reward=models.BigIntegerField(default=10)
    interst=models.CharField(max_length=40,null = True)
    visibility=models.BooleanField(default=False)
    terms_and_policy=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class skills(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE) 
    skill=models.CharField(max_length=40,)

class student_wallet(models.Model):
    student=models.OneToOneField(Student,on_delete=models.CASCADE)
    amount=models.FloatField(default=0)
# class country_name(models.Model):
#     name = models.CharField(max_length=40)

class student_information(models.Model):
    student = models.OneToOneField(Student,on_delete=models.CASCADE)
    choices=[
        ('inr','India'),
        ('aud','Australia')
        ]
    country_names=models.CharField(max_length=3,null = False,choices=choices)
    college_name = models.CharField(max_length=50,null = False)
    college_id = models.CharField(max_length=50,null = False)
    course_name = models.CharField(max_length=50,null = False)
    status = models.BooleanField(default=False)
class student_wallet_history(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    amount=models.FloatField(default=0,null = False)
    description=models.CharField(max_length=40,null = False)
    choices=[
        ('db','Debited'),
        ('cr','Credited')
        ]
    status=models.CharField(max_length=3,null = False,choices=choices)
    created_at = models.DateTimeField(auto_now_add=True)


class student_login_details(models.Model):
    student = models.OneToOneField(Student,on_delete=models.CASCADE)
    ip_address=models.GenericIPAddressField()
    old_ip_address=models.GenericIPAddressField()
    old_login_time = models.DateTimeField()
    new_login_time = models.DateTimeField(auto_now=True)
    host_name = models.CharField(max_length=50,null = False,default="NULL")
    old_host_name = models.CharField(max_length=50,null = False,default="NULL")

    
class student_favourite_program(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    program_id=models.ForeignKey(companyProgram,on_delete=models.CASCADE)



