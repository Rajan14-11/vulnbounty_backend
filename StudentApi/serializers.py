from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
import re
from MainApi.models import ExtendUser
from CompanyApi.models import submission,companyProgram
from CompanyApi.serializers import CompanyProgramSerializer
class StudentRegisterSdrializer(serializers.ModelSerializer):
    confirm_password=serializers.CharField()
    terms_and_policy=serializers.BooleanField(required=True)
    email=serializers.EmailField(required=True)
    # recaptcha = serializers.CharField(required=True)
    class Meta:
        model = User
        fields=['first_name','last_name','username','email','password','confirm_password','terms_and_policy']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password':{'write_only':True},
        }

     
    def validate(self, data):
        print("reached in validator")
        if not data.get('password') or not data.get('confirm_password'):
            raise serializers.ValidationError("Please enter a password and "
                "confirm it.")
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError("password and confirm pasword didn't match")
        return data

    def validate_email(self,email):
        # email=data["email"]
        if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
            raise serializers.ValidationError(" Email is already registered, please select another.")
        else:
            return email
    def validate_username(self,username):
        # username=data["username"]
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
    # def validate_recaptcha(self,recaptcha):
    #     secret_key=settings.RECAPTCHA_SECRET_KEY
    #     captcha_data={
    #             "secret":secret_key,
    #             "response":recaptcha
    #         }
    #     response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
    #     response=json.loads(response_data.text)
    #     verify=response['success']
    #     print(verify)
    #     if verify == True:
    #         return recaptcha
    #     else:
    #         raise serializers.ValidationError("reCAPTCHA not verifyied") 


    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        
        user.set_password(validated_data['password'])
        user.save()

        return user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=["username","first_name","last_name","email"]
class StudentDashbordserializer(serializers.ModelSerializer):
    student_user=UserSerializer(read_only=True)
    class Meta:
        model=Student
        fields="__all__"


class StudentprogramSubmissionSerializer(serializers.ModelSerializer):
    program_id=serializers.IntegerField(required=True)
    class Meta:
        model=submission
        fields=['title','report','program_id']

    def validate_program_id(self,program_id):
        if companyProgram.objects.filter(id=program_id).exists():
            return program_id
        else:
            raise serializers.ValidationError("Program not found with given id")
            
class StudentSettingsSerializer(serializers.ModelSerializer):
    student_user=UserSerializer(read_only=True)
    class Meta:
        model=Student
        fields="__all__"
    
class StudentLoginDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=student_login_details
        fields="__all__"

class StudentExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=ExtendUser
        fields="__all__"




class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model= Student
        fields=['profile_picture','profile_description']

    def create(self, validated_data):
        return  Student.objects.create(**validated_data)


# class student_skillsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model= student_skills
#         fields='__all__'

class student_walletSerializer(serializers.ModelSerializer):
    class Meta:
        model= student_wallet
        fields='__all__'

class student_informationSerializer(serializers.ModelSerializer):
    class Meta:
        model= student_information
        fields='__all__'

    def create(self, validated_data):
        return  student_information.objects.create(**validated_data)

class student_wallet_historySerializer(serializers.ModelSerializer):
    class Meta:
        model= student_wallet_history
        fields='__all__'

class student_login_detailsSerializer(serializers.ModelSerializer):
    class Meta:
        model= student_login_details
        fields='__all__'


# class student_favourite_programSerializer(serializers.ModelSerializer):
#     class Meta:
#         model= student_favourite_programs
#         fields='__all__'

class StudentChangeNameSerialzer(serializers.Serializer):
    first_name=serializers.CharField(required=True)
    last_name=serializers.CharField(required=True)
    description=serializers.CharField(required=True)

class StudentUpdateimageSerializer(serializers.ModelSerializer):
    profile_picture=serializers.ImageField(required=True)
    class Meta:
        model=Student
        fields=['profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': True},
        }
        

class StudentChangeUserNameSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(required=True)
    class Meta:
        model=User
        fields=['username','email','password']

class StudentUpdatePasswordSerializer(serializers.Serializer):
    password1=serializers.CharField()
    password2=serializers.CharField()
    password3=serializers.CharField()

class StudentSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model=skills
        fields="__all__"

class StudentSkillsAddSerializer(serializers.ModelSerializer):
    class Meta:
        model=skills
        fields=['skill']

class StudentFavouriteProgramSerializer(serializers.ModelSerializer):
    program_id=CompanyProgramSerializer(read_only=True)
    class Meta:
        model=student_favourite_program
        fields="__all__"