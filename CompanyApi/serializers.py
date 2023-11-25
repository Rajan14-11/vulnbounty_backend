from rest_framework import serializers
from django.contrib.auth.models import User
from .models import companyProgram,DropdownMenuOption,submission,ProgramCollection,company,company_login_details,company_wallet_history
from ProfessionalApi.models import professional
from StudentApi.models import Student
from MainApi.models import ExtendUser
from django.core.files.uploadedfile import UploadedFile
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
    professional_user = UserSerializer(read_only=True)
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = professional
        fields = ['user_id', 'professional_user', 'phone', 'profile_picture', 'profile_description', 'resume', 'reward', 'optional_email', 'interst']

    def get_user_id(self, obj):
        return obj.professional_user.id

class CompanyStudentLeaderBoardSerializer(serializers.ModelSerializer):
    student_user = UserSerializer(read_only=True)
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ('user_id','phone', 'profile_picture', 'profile_description', 'resume', 'reward','interst','reward','student_user')

    def get_user_id(self, obj):
        return obj.student_user.id

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
        fields=['slug','title','introduction','vulnerability_concerns','target','out_target','scope_type','severity','expiry_date','visibility','p1_min','p1_max','p2_min','p2_max','p3_min','p3_max','p4_min','p4_max','p5_min','p5_max','profile_image']


class CompanyCreateProgramSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model=companyProgram
        fields=['slug','title','introduction','vulnerability_concerns','region','visibility','severity','expiry_date','profile_image']

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

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = company
        fields = ['profile_picture']

class CompanyProgramSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    company_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = companyProgram
        exclude = ['company']

    def get_company_name(self, obj):
        return obj.company.username

    def get_company_profile_picture(self, obj):
        return CompanySerializer(obj.company).data['profile_picture']


class ProgramCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramCollection
        fields = '__all__'

class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = submission
        fields = '__all__'

class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        return data

class ResumeUploadSerializer(serializers.Serializer):
    resume = serializers.FileField()

    def validate_resume(self, value):
        allowed_extensions = ('pdf', 'doc', 'docx')
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError("Unsupported file format. Supported formats: pdf, doc, docx")

        max_file_size = 1 * 1024 * 1024
        if value.size > max_file_size:
            raise serializers.ValidationError("File size exceeds the limit of 10 MB")

        return value

class DropdownMenuOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DropdownMenuOption
        fields = ('id', 'label', 'value')
