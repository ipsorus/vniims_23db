from rest_framework import serializers


# from rest_framework import serializers
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
#
# from .models import UserProfile, SpectrumMeasurement, SpectrumField
#
#
# class UserProfileSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)
#
#     class Meta:
#         model = UserProfile
#         fields = "__all__"
#
#
# class SubmitterSerializer(serializers.ModelSerializer):
#     emailAddress = serializers.CharField()
#     firstName = serializers.CharField()
#     institution = serializers.CharField()
#
#     class Meta:
#         model = UserProfile
#         fields = ('emailAddress', 'firstName', 'institution', 'password')
#
#
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#
#     @classmethod
#     def get_token(cls, user):
#         token = super(MyTokenObtainPairSerializer, cls).get_token(user)
#
#         # Add custom claims
#         token['username'] = user.username
#         return token
#
#     class Meta:
#         model = UserProfile
#         fields = "__all__"
#
#
# class SpectrumMeasurementSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SpectrumMeasurement
#         fields = "__all__"
#
#
# class SpectrumFieldSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SpectrumField
#         fields = ['key', 'value']
