from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', db_column='user_id')
    institution = models.CharField(max_length=200)
    research_area = models.CharField(max_length=200)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email_verified = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'user_userprofile'
        managed = False  # Table already exists, Django shouldn't manage it
