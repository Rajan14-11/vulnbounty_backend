from rest_framework import serializers
from django.contrib.auth.models import User
import re

class LoginSerializer(serializers.ModelSerializer):
    username=serializers.CharField(label='Enter the user name',max_length=30,required=True)
    password=serializers.CharField(
         label=("Password"),
       
        required=True
    )
    class Meta:
        model=User
        fields=['username','password']