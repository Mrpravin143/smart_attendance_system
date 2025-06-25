from django.db import models

# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to='students/')

    def __str__(self):
        return self.name

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE,null=True,blank=True)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')],null=True,blank=True)
    timestamp = models.DateTimeField()







class LectureSchedule(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    DAYS = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
    ]    
    day_of_week = models.CharField(max_length=10,null=True,blank=True,choices=DAYS)  # e.g. 'Monday'
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject.name} ({self.day_of_week} - {self.start_time} to {self.end_time})"