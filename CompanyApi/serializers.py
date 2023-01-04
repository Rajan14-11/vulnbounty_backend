from rest_framework import serializers
from django.contrib.auth.models import User
from .models import companyProgram,submission,company,company_login_details,in_scope,rewards,out_scope
from ProfessionalApi.models import professional
from StudentApi.models import Student
from MainApi.models import ExtendUser,ValidateNumber
import re

class CompanyRegisterSerializer(serializers.ModelSerializer):
    confirm_password=serializers.CharField()
    terms_and_policy=serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields=['first_name','last_name','email','username','email','password','confirm_password']

     
    def validate(self, data):
        print("reached in validator")
        if not data.get('password') or not data.get('confirm_password'):
            raise serializers.ValidationError("Please enter a password and "
                "confirm it.")
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("Those passwords don't match.")
        return data

    def validate_email(self,data):
        email=data.get("email")
        if not email :
            raise serializers.ValidationError("Please enter email")
        else:
            if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
                raise serializers.ValidationError(" Email is already registered, please select another.")
            else:
                return email
    def validate_username(self,data):
        username=data.get("username")
        regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
        if not username:
            raise serializers.ValidationError("This field is required.")
        else:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("Username is already taken, please select another.")
            elif not re.search(regex, username):
                raise serializers.ValidationError("Allowed are alphabet,number and apostrophe") 
            else:
                return username
         
class CompanyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields="__all__"

class CompanySubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model=submission
        fields="__all__"

class CompanyProfessionalLeaderBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional
        fields="__all__"

class CompanyStudentLeaderBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model=Student
        fields="__all__"
class ComapnyImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model=company
        fields=["profile_picture"]

class CompanySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=company
        fields="__all__"

class CompanyLoginDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=company_login_details
        fields="__all__"

class CompanyExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=ExtendUser
        fields="__all__"


class CompanyCreateProgramSerializer(serializers.Serializer):
    slug=serializers.SlugField(required=True)
    title=serializers.CharField(required=True)
    introduction=serializers.CharField(required=True)
    vulnerability=serializers.CharField(required=True)
    target=serializers.URLField()
    out_target=serializers.URLField()
    scope_type=serializers.ChoiceField(
        choices=['WT','AT','IS','AD','IT','HT','OT'],required=True
    )
    visibility=serializers.ChoiceField(
        choices=['G','R','P'],required=True
    )
    p1_min=serializers.IntegerField(required=True)
    p1_max=serializers.IntegerField(required=True)
    p2_min=serializers.IntegerField(required=True)
    p2_max=serializers.IntegerField(required=True)
    p3_min=serializers.IntegerField(required=True)
    p3_max=serializers.IntegerField(required=True)
    p4_min=serializers.IntegerField(required=True)
    p4_max=serializers.IntegerField(required=True)
    p5_min=serializers.IntegerField(required=True)
    p5_max=serializers.IntegerField(required=True)
    # max_reward=serializers.IntegerField()

class CompanyCreateProgramInScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model=in_scope
        fields=['target','scope_type']

class CompanyCreateProgramOutScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model=out_scope
        fields=['out_target']

class CompanyCreateProgramRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model=rewards
        fields=['p1_min','p1_max','p2_min','p2_max','p3_min','p3_max','p4_min','p4_max','p5_min','p5_max']

class CompanyCreateProgramSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields=['slug','title','introduction','vulnerability_concerns','region','visibility']

class CompanyChangeNameSerializer(serializers.Serializer):
    first_name=serializers.CharField()
    last_name=serializers.CharField()
    description=serializers.CharField()
    
class CompanyChangeUserNameSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(required=True)
    class Meta:
        model=User
        fields=['username','email','password']

class CompanyUpdatePasswordSerializer(serializers.Serializer):
    password1=serializers.CharField()
    password2=serializers.CharField()
    password3=serializers.CharField()


