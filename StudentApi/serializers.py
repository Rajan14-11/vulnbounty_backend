from rest_framework import serializers
from StudentApi.models import *
from django.contrib.auth.models import User
import re

class StudentRegisterSdrializer(serializers.ModelSerializer):
    confirm_password=serializers.CharField()
    terms_and_policy=serializers.BooleanField(required=True)
    class Meta:
        model = User
        fields=['first_name','last_name','email','username','email','password','confirm_password']

class UserSerializer(serializers.Serializer):
    class Meta:
        fields=['first_name','last_name','username','email','password']

    def create(self, validated_data):
        return  User.objects.create(**validated_data)

    def validate_first_name(self,first_name):
        first_name=self.cleaned_data['first_name']
        if not first_name:
            raise serializers.ValidationError("This field is required.")
        if not first_name.isalpha():
            raise serializers.ValidationError("Enter a valid firstname")
        return first_name 

    def validate_last_name(self,last_name):
        last_name=self.cleaned_data['last_name']
        if not last_name:
            raise serializers.ValidationError("This field is required.")
        if not last_name.isalpha():
            raise serializers.ValidationError("Enter a valid lastname")
        return last_name

    def validate(self, username):
        username = self.cleaned_data['username']
        print(username)
        
        regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
       
        if not username:
            raise serializers.ValidationError("This field is required.")
        else:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("Username is already taken, please select another.")
            if not re.search(regex, username):
                raise serializers.ValidationError("Allowed are alphabet,number and apostrophe") 

        return username

    def validate(self, email):
        email = self.cleaned_data['email']
        if not email:
            raise serializers.ValidationError("This field is required.")
        if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
            raise serializers.ValidationError(" Email is already registered, please select another.")
        return email

    def validate(self, password ):
        password=self.cleaned_data['password']
        if self.cleaned_data['password'] != self.cleaned_data['confirm_password']:
            raise serializers.ValidationError("The passwords did not match.  Please try again.")
        return password
       

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model= Student
        fields=['profile_picture','profile_description']

    def create(self, validated_data):
        return  Student.objects.create(**validated_data)


class student_skillsSerializer(serializers.ModelSerializer):
    class Meta:
        model= student_skills
        fields='__all__'

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


class student_favourite_programSerializer(serializers.ModelSerializer):
    class Meta:
        model= student_favourite_programs
        fields='__all__'

