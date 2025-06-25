from django.contrib import admin
from attendance.models import Student,Attendance,Subject,LectureSchedule

# Register your models here.


admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(Subject)


@admin.register(LectureSchedule)
class LectureScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'start_time', 'end_time')