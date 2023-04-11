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
# class UserProfile(models.Model):
#     user = models.OneToOneField(
#         User, on_delete=models.CASCADE, related_name="profile")
#     description = models.TextField(max_length=30, blank=True)
#     location = models.CharField(max_length=30, blank=True)
#     date_joined = models.DateTimeField(auto_now_add=True)
#     updated_on = models.DateTimeField(auto_now=True)
#     is_organizer = models.BooleanField(default=False)
from django.utils import timezone


class Spectrum(models.Model):
    name = models.CharField(max_length=50, default="")
    create_date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, default=1, on_delete=models.PROTECT, related_name="author")


class SpectrumMeasurement(models.Model):
    spectrum = models.OneToOneField('Spectrum', on_delete=models.CASCADE, primary_key=True)
    source = models.IntegerField(blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    ionization = models.IntegerField(blank=True, null=True)
    polarity = models.IntegerField(blank=True, null=True)


class SpectrumField(models.Model):
    spectrum = models.OneToOneField('Spectrum', on_delete=models.CASCADE, primary_key=True)
    meta_data = models.JSONField(default=None, null=True)
    # key = models.CharField(max_length=64, blank=True, null=True)
    # value = models.CharField(max_length=64, blank=True, null=True)


class SpectrumPeak(models.Model):
    spectrum = models.OneToOneField('Spectrum', on_delete=models.CASCADE, primary_key=True)
    # spectrum = models.ForeignKey(Spectrum, on_delete=models.CASCADE, null=True)
    peaks_data = models.JSONField(default=None)
    # x = models.FloatField()
    # y = models.FloatField()
    comment = models.CharField(max_length=128, blank=True, default="")
