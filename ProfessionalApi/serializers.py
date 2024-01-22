from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from CompanyApi.models import submission
import re
from MainApi.models import ExtendUser
from CompanyApi.models import submission,companyProgram
from CompanyApi.serializers import CompanyProgramSerializer
class ProfessionalRegisterSdrializer(serializers.ModelSerializer):
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

class PrivateInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = private_invitation
        fields = '__all__'
class ProfessionalDashboardSerializer(serializers.ModelSerializer):

    class Meta:
        model = professional
        fields = '__all__'



class ProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = professional
        fields = ('id', 'invitation_preference')
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields="__all__"

class UserProfileSerializer(serializers.ModelSerializer):
    professional_user=UserSerializer(read_only=True)
    # user_id = serializers.SerializerMethodField()
    class Meta:
        model = professional
        fields = '__all__'


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'
class ProfessionalSubmissionSerialiser(serializers.ModelSerializer):
    class Meta:
        model = submission
        fields = '__all__'


class ProfessionalDashbordserializer(serializers.ModelSerializer):
    professional_user=UserSerializer(read_only=True)
    user_id = serializers.SerializerMethodField()

    class Meta:
        model=professional
        fields=['user_id','professional_user','phone','profile_picture','profile_description','resume','reward','optional_email','interst','invitation_preference']
    def get_user_id(self, obj):
        return obj.professional_user.id

class ProfessionalFavouriteProgramSerializer(serializers.ModelSerializer):
    program_id=CompanyProgramSerializer(read_only=True)
    class Meta:
        model=professional_favourite_program
        fields="__all__"

class ProfessionalprogramSubmissionSerializer(serializers.ModelSerializer):
    program_id=serializers.IntegerField(required=True)
    class Meta:
        model=submission
        fields=['title','report','program_id','asset','severity','description','impact','weakness']

    def validate_program_id(self,program_id):
        if companyProgram.objects.filter(id=program_id).exists():
            return program_id
        else:
            raise serializers.ValidationError("Program not found with given id")


    # def create(self, validated_data):
    #     user = submission.objects.create(
    #         title=validated_data['title'],
    #         report=validated_data['report'],
    #         first_name=validated_data['first_name'],
    #         last_name=validated_data['last_name']
    #     )


    #     user.set_password(validated_data['password'])
    #     user.save()

    #     return user
class UserSelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSelection
        fields = '__all__'
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

class ProfessionalChangeNameSerialzer(serializers.Serializer):
    first_name=serializers.CharField(required=True)
    last_name=serializers.CharField(required=True)
    description=serializers.CharField(required=True)



class ProfessionalUpdateimageSerializer(serializers.ModelSerializer):
    profile_picture=serializers.ImageField(required=True)
    class Meta:
        model=professional
        fields=['profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': True},
        }


class ProfessionalUpdateResumeSerializer(serializers.ModelSerializer):
    resume=serializers.FileField(required=True)
    class Meta:
        model=professional
        fields=['resume']
        extra_kwargs = {
            'resume': {'required': True},
        }
    def validate_resume(self,resume):
        print("reached")
        if not resume:
            raise serializers.ValidationError("This field is required.")
        else:
            return resume

class ProfessionalSkillsAddSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_skills
        fields=['skill']

class ProfessionalSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_skills
        fields="__all__"

class ProfessionalSettingsSerializer(serializers.ModelSerializer):
    professional_user=UserSerializer(read_only=True)
    class Meta:
        model=professional
        fields="__all__"

class ProfessionalLoginDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_login_details
        fields="__all__"

class ProfessionalExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=ExtendUser
        fields="__all__"

class ProfessionalChangeUserNameSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(required=True)
    class Meta:
        model=User
        fields=['username','email','password']

class ProfessionalUpdatePasswordSerializer(serializers.Serializer):
    password1=serializers.CharField()
    password2=serializers.CharField()
    password3=serializers.CharField()

class professionalInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_information
        fields=['country_names']

class ProfessionalPaymentSerializer(serializers.Serializer):
    withdraw_amount = serializers.IntegerField(required=True)
class ProfessionalTestSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_test
        fields=['question','answer']

class ProfessionalSerializer(serializers.ModelSerializer):
    professional_user=UserSerializer(read_only=True)
    user_id = serializers.SerializerMethodField()
    class Meta:
        model = professional
        fields = '__all__'

    def get_user_id(self, obj):
        return obj.professional_user.id

class FollowerSerializer(serializers.ModelSerializer):
    professional = ProfessionalSerializer()
    class Meta:
        model = Follower
        fields = '__all__'

class UpdateProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = professional
        fields = '__all__'
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = professional
        fields = '__all__'
# class UserProfileUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserProfile
#         fields = ['name', 'username', 'website_link', 'location', 'country', 'language', 'about_me', 'profile_picture']

class ProfessionalBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalBankDetail
        # fields = '__all__'
        fields = ['account_number','bank_name','account_holder_name','balance']

class ProfessionalWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalWallet
        fields = '__all__'


class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = '__all__'
