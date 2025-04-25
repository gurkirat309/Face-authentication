from django.db import models
from django.contrib.auth.models import User

class UserImages(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    face_image = models.ImageField(upload_to='user_faces/')
    face_encoding = models.BinaryField(null=True)

    def __str__(self):
        return self.user.username

# models.py
class Vote(models.Model):
    candidate = models.CharField(max_length=255)
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} voted for {self.choice}"

    class Meta:
        ordering = ['-timestamp']
