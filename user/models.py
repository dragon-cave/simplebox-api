from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True, blank=True)
    profile_picture = models.URLField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)