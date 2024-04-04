from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class ExtendUser(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    optional_email=models.EmailField(null=True)
    optional_email_token=models.CharField(max_length=100,null=False,default="null")
    optional_email_status=models.BooleanField(default=False)
class ValidateNumber(models.Model):
    user=models.OneToOneField(ExtendUser,on_delete=models.CASCADE)
    message_id=models.CharField(max_length=100,null=False)
    phone_number=models.IntegerField(max_length=20,null=False)
    code = models.IntegerField(max_length=20,null=False)
    status=models.BooleanField(default=False)

class messages(models.Model):
    submission_id= models.IntegerField()
    sender_id = models.IntegerField()
    receiver_id = models.IntegerField()
    text = models.CharField(max_length=1200)
    created_at = models.DateTimeField(auto_now_add=True)


class UserToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500)
