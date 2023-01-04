from django.contrib.auth.models import User
from django.db import models
from django.core.validators import validate_image_file_extension
from django.core.validators import FileExtensionValidator
from django.conf import settings
from CompanyApi.models import companyProgram
# Create your models here.
class professional(models.Model):
    professional_user = models.ForeignKey(User,on_delete=models.CASCADE)
    phone=models.IntegerField(null = True)
    profile_picture=models.ImageField(null = True,blank = True,upload_to='professional/images/profile_picture',default='Null',validators=[validate_image_file_extension])
    profile_description=models.CharField(null = True,max_length=60)
    resume = models.FileField(null = True,blank = True,upload_to='professional/document/resume' ,default='Null',validators=[FileExtensionValidator(['pdf'])])
    reward=models.BigIntegerField(default=10)
    forget_password_token=models.CharField(max_length=100,null=True)
    optional_email=models.EmailField()
    email_verification_token =models.CharField(max_length=100,null=True)
    email_status = models.BooleanField(default=False) 
    interst=models.CharField(max_length=40,null = True)
    terms_and_policy=models.BooleanField(default=False)
    visibility=models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class professional_skills(models.Model):
    user=models.ForeignKey(professional,on_delete=models.CASCADE)
    skill=models.CharField(max_length=40,)

class professional_socialmedia(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    title=models.CharField(max_length=30)
    links=models.URLField()

class professional_wallet(models.Model):
    professional=models.OneToOneField(professional,on_delete=models.CASCADE)
    amount=models.FloatField(default=0)
class professional_wallet_history(models.Model):
    professional= models.ForeignKey(professional,on_delete=models.CASCADE)
    amount=models.FloatField(default=0,null = False)
    description=models.CharField(max_length=40,null = False)
    choices=[
        ('db','Debited'),
        ('cr','Credited')
        ]
    status=models.CharField(max_length=3,null = False,choices=choices)
    created_at = models.DateTimeField(auto_now_add=True)
class professional_information(models.Model):
    professional = models.OneToOneField(professional,on_delete=models.CASCADE)
    choices=[
        ('inr','India'),
        ('aud','Australia')
        ]
    country_names=models.CharField(max_length=3,null = False,choices=choices)
    status = models.BooleanField(default=False)
class professional_login_details(models.Model):
    professional=models.OneToOneField(professional,on_delete=models.CASCADE)
    ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_login_time = models.DateTimeField()
    new_login_time = models.DateTimeField(auto_now=True)
    host_name = models.CharField(max_length=50,null = False,default="NULL")
    old_host_name = models.CharField(max_length=50,null = False,default="NULL")

class professional_favourite_program(models.Model):
    professional = models.ForeignKey(professional,on_delete=models.CASCADE)
    program_id =models.ForeignKey(companyProgram,on_delete=models.CASCADE)

