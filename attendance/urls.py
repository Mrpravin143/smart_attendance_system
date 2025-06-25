from django.urls import path
from attendance.views import register_student,success_user,admin_dashboard,schedule_list_create,delete_schedule

urlpatterns =[

    path('',register_student),
    path('success-user/',success_user,name='success_user'),
    path('admin-dashboard/',admin_dashboard,name='admin_dashboard'),
    path('schedule/',schedule_list_create,name='schedule_list_create'),
    path('schedule/delete/<int:pk>',delete_schedule,name='delete_schedule'),

    
    ]