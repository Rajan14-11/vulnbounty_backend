from django.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_image_file_extension
from django.core.validators import FileExtensionValidator,MinValueValidator
from django.utils import timezone
from django.apps import apps
from django.conf import settings

class company(models.Model):
    company_user=models.OneToOneField(User,on_delete=models.CASCADE,default="")
    company_name=models.CharField(max_length=100, null=True)
    profile_picture=models.ImageField(upload_to='company/images/profile_picture',default='Null' ,blank=True, null=True,validators=[validate_image_file_extension])
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
class company_wallet_history(models.Model):
    company= models.ForeignKey(company,on_delete=models.CASCADE)
    amount=models.FloatField(default=0,null = False)
    description=models.CharField(max_length=40,null = False,default="description")
    recived_from=models.ForeignKey(User,on_delete=models.CASCADE,null = True)
    choices=[
        ('db','Debited'),
        ('cr','Credited')
        ]
    status=models.CharField(max_length=3,null = False,choices=choices,default='none')
    created_at = models.DateTimeField(auto_now_add=True)

class company_login_details(models.Model):
    company=models.OneToOneField(company,on_delete=models.CASCADE)
    ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_ip_address=models.GenericIPAddressField(default="92.0.2.0")
    old_login_time = models.DateTimeField()
    new_login_time = models.DateTimeField(auto_now=True)
    host_name = models.CharField(max_length=50,null = False,default="NULL")
    old_host_name = models.CharField(max_length=50,null = False,default="NULL")

class companyProgram(models.Model):
    company = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=30)
    profile_image = models.ImageField(
        upload_to='company_profiles/', null=True, blank=True)
    title = models.CharField(max_length=100, default="Company Name", blank=True)
    introduction = models.TextField(max_length=1000, blank=True, default='A bug bounty program')
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    choices = [
        ('G', 'Global'),
        ('R', 'Regional'),
        ('P', 'Private'),
    ]
    vulnerability_concerns = models.TextField(max_length=1000,)
    region = models.CharField(max_length=3, default='all')
    visibility = models.CharField(max_length=1, choices=choices, default='G')
    target = models.URLField(max_length=200, null=True, default="http://test.com")
    scope_choices = [
        ('WT', 'Website Testing'),
        ('AT', 'API Testing'),
        ('IS', 'iOS Application'),
        ('AD', 'Android Application'),
        ('IT', 'IoT Testing'),
        ('HT', 'Hardware Testing'),
        ('OT', 'Others')
    ]
    scope_type = models.CharField(max_length=2, choices=scope_choices, default='OT')
    out_target = models.URLField(max_length=200, null=True, default="http://test.com")
    p1_min = models.PositiveIntegerField(null=True, blank=False)
    p1_max = models.PositiveIntegerField(null=True, blank=False)
    p2_min = models.PositiveIntegerField(null=True, blank=False)
    p2_max = models.PositiveIntegerField(null=True, blank=False)
    p3_min = models.PositiveIntegerField(null=True, blank=False)
    p3_max = models.PositiveIntegerField(null=True, blank=False)
    p4_min = models.PositiveIntegerField(null=True, blank=False)
    p4_max = models.PositiveIntegerField(null=True, blank=False)
    p5_min = models.PositiveIntegerField(null=True, blank=False)
    p5_max = models.PositiveIntegerField(null=True, blank=False)
    policy = models.TextField(null=True,blank=False)
    max_reward = models.PositiveIntegerField(null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='Low')
    expiry_date = models.DateField(null=True, blank=False, validators=[MinValueValidator(limit_value=timezone.now().date())])
    posted = models.BooleanField(default=False)
    created_at = models.DateField(auto_now=True)
    edited_at = models.DateField(auto_now=True)


class submission(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    program=models.ForeignKey(companyProgram,on_delete=models.CASCADE,null=True)
    title = models.CharField(max_length=199)

    choices=[
        ('Low','Low'),
        ('Mid','Mid'),
        ('High','High'),
        ('Critical','Critical'),
    ]
    severity = models.CharField(max_length=10,choices=choices,null=True)
    report = models.FileField(upload_to='document/report',validators=[FileExtensionValidator(['pdf'])])
    description= models.CharField(max_length=199,null=True)
    impact = models.CharField(max_length=100,null=True)
    asset = models.CharField(max_length=100,null=True)
    weakness = models.CharField(max_length=100,null=True)

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

class ScopeEntry(models.Model):
    program = models.ForeignKey(companyProgram, on_delete=models.CASCADE, related_name='scope_entries')
    asset_name = models.CharField(max_length=100, blank=True)
    asset_description = models.TextField(max_length=1000, blank=True)
    ASSET_TYPE_CHOICES = [
        ('Sourcecode', 'Sourcecode'),
        ('OtherAsset', 'OtherAsset'),
        ('AndroidApk','AndroidApk'),
        ('Wildcard','Wildcard'),
        ('Domain','Domain'),
    ]
    type = models.CharField(max_length=10, choices=ASSET_TYPE_CHOICES, default='Type1')
    COVERAGE_CHOICES = [
        ('In Scope', 'In Scope'),
        ('Out of Scope', 'Out of Scope'),
    ]
    coverage = models.CharField(max_length=27, choices=COVERAGE_CHOICES, default='Partial')
    MAX_SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Mid', 'Mid'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    max_severity = models.CharField(max_length=10, choices=MAX_SEVERITY_CHOICES, default='Low')
    BOUNTY_CHOICES = [
        ('Points', 'Points'),
        ('Rewards', 'Rewards'),
    ]
    bounty = models.CharField(max_length=7, choices=BOUNTY_CHOICES, default='Points')
    created_at = models.DateField(auto_now=True)
    def __str__(self):
        return f"{self.asset_name} - {self.program.title}"

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

class ProgramCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(companyProgram, on_delete=models.CASCADE)

class DropdownMenuOption(models.Model):
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    is_custom = models.BooleanField(default=False)

    def __str__(self):
        return self.label

class CompanyWallet(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    company = models.ForeignKey(company, on_delete=models.CASCADE, related_name='company_personal_wallet')
    stripe_account_id = models.CharField(max_length=255,null=True)
    stripe_transaction_id = models.CharField(max_length=255, null=True, blank=True)

class CompanyBankDetail(models.Model):
    company = models.ForeignKey(company, on_delete=models.CASCADE, related_name='company_bank_details')
    account_number = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stripe_charge_id = models.CharField(max_length=255, null=True, blank=True)


class Transaction(models.Model):
    payment_id = models.CharField(
        max_length=200, verbose_name="Payment ID", default='')
    order_id = models.CharField(
        max_length=200, verbose_name="Order ID", default='')
    signature = models.CharField(
        max_length=500, verbose_name="Signature", blank=True, null=True)
    amount = models.IntegerField(verbose_name="Amount")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)
