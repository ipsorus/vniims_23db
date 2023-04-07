from pyexpat import model
from statistics import mode
from django.contrib.auth.models import User
from django.db import models


# class UserProfile(models.Model):
#
#     # firstName = models.OneToOneField(User, on_delete=models.PROTECT)
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
#     firstName = models.CharField(max_length=100)
#     lastName = models.CharField(max_length=100)
#     institution = models.CharField(max_length=100)
#     emailAddress = models.EmailField(unique=True, max_length = 200)
#     password = models.CharField(max_length=100)
#     passwordMatch = models.CharField(max_length=100)
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4)
#
#     def __str__(self):
#         return f"Submitter: {self.firstName}, {self.emailAddress}"
class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    description = models.TextField(max_length=30, blank=True)
    location = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_organizer = models.BooleanField(default=False)


class SpectrumMeasurement(models.Model):
    source = models.IntegerField(blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    ionization = models.IntegerField(blank=True, null=True)
    polarity = models.IntegerField(blank=True, null=True)


class SpectrumField(models.Model):
    measurement = models.ForeignKey(
        SpectrumMeasurement, on_delete=models.CASCADE)
    key = models.CharField(max_length=64, blank=True, null=True)
    value = models.CharField(max_length=64, blank=True, null=True)


class SpectrumPeak(models.Model):
    measurement = models.ForeignKey(
        SpectrumMeasurement, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    comment = models.CharField(max_length=128, blank=True, default="")
