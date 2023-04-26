from rest_framework import serializers
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from StudentApi.models import Student,student_login_details
from CompanyApi.models import company,company_login_details
from ProfessionalApi.models import professional,professional_login_details
from .models import ValidateNumber
class LoginSerializer(serializers.Serializer):
    username=serializers.CharField()
    password=serializers.CharField()
    def validate(self, data):
        username=data.get('username')
        password=data.get('password')
        if username and password:
            user =authenticate(username=username, password=password)
            if user is not None:
                if Student.objects.filter(student_user=user.id,email_status=False).exists():
                    raise serializers.ValidationError("Verify your email to Login") 
                elif professional.objects.filter(professional_user=user.id,email_status=False).exists():
                    raise serializers.ValidationError("Verify  your email to Login") 
                elif company.objects.filter(company_user=user.id,email_status=False).exists():
                    raise serializers.ValidationError("Verify  your email to Login") 
                else: 
                    return data
            else:
                raise serializers.ValidationError("Username and Password doesn't match")
        else:
            raise serializers.ValidationError("Must include username and password")
    def validate_username(self,username):
        if not username:
            raise serializers.ValidationError("Username  is required.")
        else:
            return username
    def validate_password(self,password):
        if not password:
            raise serializers.ValidationError("Password is required.")
        else:
            return password
   
    

class ValidatePhoneSerializer(serializers.Serializer):
    country_code=serializers.CharField()
    phone_number=serializers.IntegerField()

class PhoneValidation(serializers.ModelSerializer):
    class Meta:
        model=ValidateNumber
        fields=["code","status","phone_number"]