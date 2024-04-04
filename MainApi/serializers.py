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
    remember_me = serializers.BooleanField(default=False)
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

    def error_handle(errors):
        error_messages = []
        for field, field_errors in errors.items():
            for error in field_errors:
                error_messages.append(f"{field}: {error}")

        return {"errors": error_messages}


class ValidatePhoneSerializer(serializers.Serializer):
    country_code=serializers.CharField()
    phone_number=serializers.IntegerField()

class PhoneValidation(serializers.ModelSerializer):
    class Meta:
        model=ValidateNumber
        fields=["code","status","phone_number"]

class ForgotPasswordSerializer(serializers.Serializer):
    email=serializers.EmailField()

class ChangePasswordSerializer(serializers.Serializer):
    password=serializers.CharField(required=True)
    confirm_password=serializers.CharField(required=True)
    token=serializers.CharField(required=True)