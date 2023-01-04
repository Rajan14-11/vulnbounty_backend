from rest_framework import serializers
from django.contrib.auth.models import User
from .models import professional,professional_favourite_program,professional_skills

class ProfessionalRegisterSdrializer(serializers.ModelSerializer):
    confirm_password=serializers.CharField()
    terms_and_policy=serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields=['first_name','last_name','email','username','email','password','confirm_password']



class ProfessionalDashbordserializer(serializers.ModelSerializer):
    class Meta:
        model=professional
        fields="__all__"

class ProfessionalFavouriteProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_favourite_program
        fields="__all__"

# class ProfessionalprogramSubmissionSerializer(serializers.ModelSerializer):
#     class Meat:
#         model=professional_program_submission
#         fields=['submission']

class ProfessionalChangeNameSerialzer(serializers.Serializer):
    first_name=serializers.CharField(required=True)
    last_name=serializers.CharField(required=True)
    description=serializers.CharField(required=True)

  

class ProfessionalUpdateimageSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional
        fields=['profile_picture']

class ProfessionalUpdateResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional
        fields=['resume']

class ProfessionalSkillsAddSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_skills
        fields=['skill']

class ProfessionalSkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model=professional_skills
        fields="__all__"
