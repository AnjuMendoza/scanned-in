from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    professor = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"