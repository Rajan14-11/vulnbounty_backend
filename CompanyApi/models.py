from django.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_image_file_extension
from django.core.validators import FileExtensionValidator
from django.conf import settings
# from ProfessionalApi.models import professional

class company(models.Model):
    company_user=models.ForeignKey(User,on_delete=models.CASCADE,default="")
    company_name=models.CharField(max_length=100, null=True)
    profile_picture=models.ImageField(upload_to='company/images/profile_picture',default='Null' , null=True,validators=[validate_image_file_extension])
    background_picture=models.ImageField(upload_to='company/',default='/image.png', null=True)
    description=models.CharField(max_length=200,null=True)
    forget_password_token=models.CharField(max_length=100,null=True)
    email_verification_token =models.CharField(max_length=100,null=True)
    email_status = models.BooleanField(default=False) 
    visibility = models.BooleanField(default=True)
    terms_and_policy=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

class company_wallet(models.Model):
    company = models.OneToOneField(company,on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class company_login_details(models.Model):
    company=models.OneToOneField(company,on_delete=models.CASCADE)
    ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_login_time = models.DateTimeField()
    new_login_time = models.DateTimeField(auto_now=True)
    host_name = models.CharField(max_length=50,null = False,default="NULL")
    old_host_name = models.CharField(max_length=50,null = False,default="NULL")
class in_scope(models.Model):
    target=models.URLField(max_length=200,)
    choices=[
        ('WT','Website Testing'),
        ('AT','API Testing'),
        ('IS','iOS Application'),
        ('AD','Android Application'),
        ('IT','IoT Testing'),
        ('HT','Hardware Testing'),
        ('OT','Others')
    ]
    scope_type=models.CharField( max_length=2,choices=choices,default='OT')
class tags(models.Model):
    choices=[
        ('WT','Website Testing'),
        ('AT','API Testing'),
        ('IS','iOS Application'),
        ('AD','Android Application'),
        ('IT','IoT Testing'),
        ('HT','Hardware Testing'),
        ('OT','Others')
    ]
    scope_type=models.CharField( max_length=2,choices=choices,default='OT')
    tag=models.CharField(max_length=100)

class out_scope(models.Model):
    out_target=models.URLField(max_length=200)
class rewards(models.Model):
    p1_min=models.PositiveIntegerField(null=False,blank=False)
    p1_max=models.PositiveIntegerField(null=False,blank=False)
    p2_min=models.PositiveIntegerField(null=False,blank=False)
    p2_max=models.PositiveIntegerField(null=False,blank=False)
    p3_min=models.PositiveIntegerField(null=False,blank=False)
    p3_max=models.PositiveIntegerField(null=False,blank=False)
    p4_min=models.PositiveIntegerField(null=False,blank=False)
    p4_max=models.PositiveIntegerField(null=False,blank=False)
    p5_min=models.PositiveIntegerField(null=False,blank=False)
    p5_max=models.PositiveIntegerField(null=False,blank=False)
    max_reward=models.PositiveIntegerField(null=True,blank=True)


class companyProgram(models.Model):
    company=models.ForeignKey(User, on_delete=models.CASCADE)
    slug=models.SlugField(max_length=30)
    title=models.CharField(max_length=100,default="Company Name ",blank=True)
    introduction=models.TextField(max_length=1000,blank=True,default='A bug bounty program')
    choices=[
        ('G','Global'),
        ('R','Regional'),
        ('P','Private'),
    ]
    vulnerability_concerns=models.TextField(max_length=1000,null=True)
    region=models.CharField(max_length=3,default='all')
    visibility=models.CharField(max_length=1,choices=choices,default='G')
    in_scope=models.ForeignKey(in_scope, on_delete=models.CASCADE,null=True)
    out_scope=models.ForeignKey(out_scope,on_delete=models.CASCADE,null=True)
    rewards=models.ForeignKey(rewards,on_delete=models.CASCADE,null=True)
    posted=models.BooleanField(default=False)
    creation_step=models.IntegerField(default=0)
    created_at=models.DateField(auto_now_add=True)
    edited_at=models.DateField(auto_now=True)


class submission(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    program=models.ForeignKey(companyProgram,on_delete=models.CASCADE,null=True)
    title = models.CharField(max_length=199)
   
    # choices=[
    #     ('L','Low'),
    #     ('M','Medium'),
    #     ('H','High'),
    #     ('C','Critical'),
    # ]
    # severity = models.CharField(max_length=1,choices=choices)
    report = models.FileField(upload_to='document/report',validators=[FileExtensionValidator(['pdf'])])
    # description= models.CharField(max_length=199)
    # additional_information = models.CharField(max_length=100)
    
    status = models.CharField(max_length=50,default="pending")
    payment_status=models.BooleanField(null=True,default=False)
    payment_amount=models.FloatField(null=True)
    location=models.CharField(max_length=50,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# class private_invitation(models.Model):
#     program=models.ForeignKey(companyProgram,on_delete=models.CASCADE)
#     hunter=models.ForeignKey(professional, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

class payments(models.Model):
    choices=[
        ('P1','P1 min - P1 max'),
        ('P2','P2 min - P2 max'),
        ('P3','P3 min - P3 max'),
        ('P4','P4 min - P4 max'),
        ('P5','P5 min - P5 max'),
        ('MR','Max Reward')
    ]
    reward=models.CharField(max_length=2,choices=choices,null=False)
    transfer_from = models.ForeignKey(company,on_delete=models.CASCADE)
    transfer_to = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)