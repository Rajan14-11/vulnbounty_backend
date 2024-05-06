from django.contrib.auth.models import User
from django.db import models
from django.core.validators import validate_image_file_extension
from django.core.validators import FileExtensionValidator
from django.conf import settings
from CompanyApi.models import companyProgram
from multiselectfield import MultiSelectField
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.utils import timezone
import uuid
# Create your models here.
class professional(models.Model):
    professional_user = models.OneToOneField(User,related_name='professional_user',on_delete=models.CASCADE)
    phone=models.IntegerField(null = True)
    profile_picture=models.ImageField(null = True,blank = True,upload_to='professional/images/profile_picture',default='Null',validators=[validate_image_file_extension])
    profile_description=models.CharField(null = True,max_length=60)
    resume = models.FileField(null = True,blank = True,upload_to='professional/document/resume' ,default='Null',validators=[FileExtensionValidator(['pdf'])])
    reward=models.BigIntegerField(default=10)
    forget_password_token=models.CharField(max_length=100,null=True)
    optional_email=models.EmailField(null=True)
    email_verification_token =models.CharField(max_length=100,null=True)
    email_status = models.BooleanField(default=False)
    interst=models.CharField(max_length=40,null = True)
    terms_and_policy=models.BooleanField(default=False)
    visibility=models.BooleanField(default=True)
    test_status=models.BooleanField(default=False,null=True)
    invitation_preference = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    website_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    bugcrowd_handle = models.CharField(max_length=50, blank=True, null=True)
    cobalt_handle = models.CharField(max_length=50, blank=True, null=True)
    linkedin_handle = models.CharField(max_length=50, blank=True, null=True)
    twitter_handle = models.CharField(max_length=50, blank=True, null=True)
    hack_the_box_handle = models.CharField(max_length=50, blank=True, null=True)
    intro = models.TextField(blank=True, null=True)
    employment_type = models.CharField(max_length=40,default="open_for_employemnt")
    questions_completed = models.BooleanField(default=False)

class professional_skills(models.Model):
    user=models.ForeignKey(professional,on_delete=models.CASCADE)
    skill=models.CharField(max_length=40,)

class private_invitation(models.Model):
    program=models.ForeignKey(companyProgram,on_delete=models.CASCADE)
    hunter=models.ForeignKey(professional, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Certificate(models.Model):
    user = models.ForeignKey(professional, on_delete=models.CASCADE, null=True)

    certificate_name = models.CharField(max_length=255)
    organisations = models.CharField(max_length=255)
    issues_date = models.DateField()
    expiry_date = models.DateField()
    certificate_id = models.CharField(max_length=255,default=uuid.uuid4)
    certificate_url = models.URLField()

    def __str__(self):
        return self.certificate_name
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
    recived_from=models.ForeignKey(User,on_delete=models.CASCADE,null = True)
    choices=[
        ('db','Debited'),
        ('cr','Credited')
        ]
    status=models.CharField(max_length=3,null = False,choices=choices)
    created_at = models.DateTimeField(auto_now_add=True)


class professional_razorpay_account(models.Model):
    professional = models.ForeignKey(professional, on_delete=models.CASCADE, null=True)
    acc_id = models.CharField(max_length=30, null=True, unique=True)

class Follower(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    professional = models.ForeignKey(professional, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

class professional_information(models.Model):
    professional = models.OneToOneField(professional,on_delete=models.CASCADE)
    choices=[
        ('inr','India'),
        ('aud','Australia')
        ]
    country_names=models.CharField(max_length=3,null = False,choices=choices)
    status = models.BooleanField(default=False)

class QuizQuestion(models.Model):
    question = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E')])

class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E')])

class ResumeModel(models.Model):
    file_content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

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

class professional_test(models.Model):
    question=models.TextField()
    answer=models.TextField()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    website_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    bugcrowd_handle = models.CharField(max_length=50, blank=True, null=True)
    cobalt_handle = models.CharField(max_length=50, blank=True, null=True)
    linkedin_handle = models.CharField(max_length=50, blank=True, null=True)
    twitter_handle = models.CharField(max_length=50, blank=True, null=True)
    hack_the_box_handle = models.CharField(max_length=50, blank=True, null=True)
    intro = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(blank=True, null=True, upload_to='user_profiles/', default='default_profile_picture.png')

class UserSelection(models.Model):
    user= models.OneToOneField(
        professional, on_delete=models.CASCADE,null=True, related_name='user_quiz')
    question_1 = models.JSONField(null=True)
    question_2 = models.CharField(max_length=255, null=True)
    question_3 = models.JSONField(null=True)
    question_4 = models.CharField(max_length=255, null=True)
    question_5 = models.JSONField(null=True)

class ProfessionalBankDetail(models.Model):
    professional = models.ForeignKey(professional, on_delete=models.CASCADE, related_name='bank_details')
    account_number = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

class ProfessionalWalletManager(models.Manager):
    def get_wallet(self, professional):
        try:
            return self.get(professional=professional)
        except ObjectDoesNotExist:
            return None

class ProfessionalWallet(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    professional = models.OneToOneField(professional, on_delete=models.CASCADE, related_name='wallet')

    objects = ProfessionalWalletManager()

