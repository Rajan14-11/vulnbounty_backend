from rest_framework import serializers
from django.contrib.auth.models import User
from .models import companyProgram,submission,company,company_login_details,company_wallet_history
from ProfessionalApi.models import professional
from StudentApi.models import Student
from MainApi.models import ExtendUser
import re
# from rest_framework_recaptcha import ReCaptchaField



# class MyReCaptchaField(ReCaptchaField):
#     default_error_messages = {
#         "invalid-input-response": "reCAPTCHA token is invalid.",
#     }


class CompanyRegisterSerializer(serializers.ModelSerializer):
    confirm_password=serializers.CharField()
    email=serializers.EmailField(required=True)
    # recaptcha = serializers.CharField(required=True)
    class Meta:
        model = User
        fields=['first_name','last_name','username','email','password','confirm_password']
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

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields="__all__"

class CompanyProgramSerializer(serializers.ModelSerializer):
    company=UserSerializer(read_only=True)
    class Meta:
        model=companyProgram
        fields="__all__"

class CompanySubmissionSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    program=CompanyProgramSerializer(read_only=True)
    class Meta:
        model=submission
        fields="__all__"

class CompanyProfessionalLeaderBoardSerializer(serializers.ModelSerializer):
    professional_user=UserSerializer(read_only=True)
    class Meta:
        model=professional
        fields=['professional_user','phone','profile_picture','profile_description','resume','reward','optional_email','interst']

class CompanyStudentLeaderBoardSerializer(serializers.ModelSerializer):
    student_user=UserSerializer(read_only=True)
    class Meta:
        model=Student
        fields="__all__"
class ComapnyImageUploadSerializer(serializers.ModelSerializer):
    profile_picture=serializers.ImageField(required=True)
    class Meta:
        model=company
        fields=["profile_picture"]
        extra_kwargs = {
            'profile_picture': {'required': True},
        }
    def validate(self,data):
        if not data.get('profile_picture') :
            raise serializers.ValidationError({"profile_picture":"This field is required."})
        else:
            return data


class CompanySettingsSerializer(serializers.ModelSerializer):
    company_user=UserSerializer(read_only=True)
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


class CompanyCreateProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields=['slug','title','introduction','vulnerability_concerns','target','out_target','scope_type','visibility','p1_min','p1_max','p2_min','p2_max','p3_min','p3_max','p4_min','p4_max','p5_min','p5_max']


class CompanyCreateProgramSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields=['slug','title','introduction','vulnerability_concerns','region','visibility']

class CompanyChangeNameSerializer(serializers.Serializer):
    first_name=serializers.CharField()
    last_name=serializers.CharField()
    description=serializers.CharField()

class CompanyChangeUserNameSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)
    username=serializers.CharField(required=True)
    password=serializers.CharField(required=True)


class CompanyUpdatePasswordSerializer(serializers.Serializer):
    password1=serializers.CharField()
    password2=serializers.CharField()
    password3=serializers.CharField()


class CompanyWalletHistory(serializers.ModelSerializer):
    company=CompanySettingsSerializer(read_only=True)
    recived_from=UserSerializer(read_only=True)
    class Meta:
        model=company_wallet_history
        fields=['company',"amount",'description','recived_from','status','created_at']

# class CompanyProgramSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = companyProgram
#         fields = '__all__'

class CompanyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = companyProgram
        exclude = ['company']