from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from attendance.models import Student,Attendance,Subject,LectureSchedule
from django.contrib import messages
import subprocess
from django.core.files.storage import FileSystemStorage
import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime,time,timedelta
from django.db.models import Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import csv
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.utils import timezone
from django.db.models import Max


# Create your views here.


def register_student(request):
    if request.method == "POST":
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        photo = request.FILES.get('photo')

        Student.objects.create(
            name=name,
            student_id=student_id,
            photo=photo,
        )
        messages.success(request, "Student Registraion Success ! 🤗")
        return redirect('/success-user/')


    return render(request,'register_student.html')

    

def success_user(request):
    student_id = request.session.get('student_id')
    return render(request, 'success.html', {'student_id': student_id})

    


# ✅ Capture Face View
def capture_face_ui(request, student_id):
    return render(request, 'capture.html', {'student_id': student_id})


# ✅ Train Model View
def train_model_ui(request):
    # Call trainer logic here (same as trainer.py)
    from .trainer_logic import train_model  # You should move trainer code to separate file
    train_model()
    return render(request, 'train.html')


def manual_capture_backend(request, student_id):
    from .manual_capture import manual_face_capture
    manual_face_capture(student_id)
    return redirect('/train/')






# ✅ Helper Function

def get_current_lecture_subject():
    now = datetime.now().time()
    current_day = datetime.now().strftime('%A')

    lecture = LectureSchedule.objects.filter(
        day_of_week=current_day,
        start_time__lte=now,
        end_time__gte=now
    ).select_related('subject').first()

    if lecture:
        return lecture
    return None


def mark_absent_for_non_detected_students(detected_student_ids, subject):
    today = timezone.now().date()
    
    # ✅ सर्व students from Student model
    all_students = Student.objects.all()

    for student in all_students:
        # फक्त जे detect झाले नाहीत त्यांच्यासाठी:
        if str(student.student_id) not in detected_student_ids:
            # Check already exists
            exists = Attendance.objects.filter(
                student=student,
                subject=subject,
                timestamp__date=today
            ).exists()
            if not exists:
                Attendance.objects.create(
                    student=student,
                    subject=subject,
                    status="Absent",
                    timestamp=timezone.now()
                )
                print(f"❌ Absent marked for {student.name}")


# ✅ Admin Dashboard View

def admin_dashboard(request):
    subjects = Subject.objects.all()
    attendance_list = Attendance.objects.select_related('student', 'subject').all()

    # ✅ Filters
    selected_date = request.GET.get('date')
    selected_subject = request.GET.get('subject')
    export_type = request.GET.get("export")

    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            attendance_list = attendance_list.filter(timestamp__date=date_obj)
        except:
            pass

    if selected_subject:
        attendance_list = attendance_list.filter(subject__id=selected_subject)

    # ✅ Group by latest entry per student+subject per day
    grouped_records = attendance_list.values(
        'student__student_id', 'student__name', 'subject__name'
    ).annotate(
        latest_time=Max('timestamp')
    )

    unique_attendance = []
    for record in grouped_records:
        att = Attendance.objects.filter(
            student__student_id=record['student__student_id'],
            subject__name=record['subject__name'],
            timestamp=record['latest_time']
        ).first()
        if att:
            unique_attendance.append(att)

    # ✅ Current Lecture Logic
    current_lecture = get_current_lecture_subject()
    remaining_minutes = None

    if current_lecture:
        now = datetime.now()
        end_datetime = datetime.combine(now.date(), current_lecture.end_time)
        remaining_minutes = int((end_datetime - now).total_seconds() // 60)

    # ✅ Export Logic
    if export_type:
        export_data = []
        for att in unique_attendance:
            export_data.append({
                'Student Name': att.student.name,
                'Student ID': att.student.student_id,
                'Subject': att.subject.name if att.subject else '',
                'Status': att.status,
                'Date': att.timestamp.strftime("%Y-%m-%d %H:%M")
            })

        if export_type == "excel":
            df = pd.DataFrame(export_data)
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="attendance.xlsx"'
            with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Attendance")
            return response

        elif export_type == "pdf":
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="attendance.pdf"'

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph("\ud83d\udcca Attendance Report", styles['Title']))
            if selected_date:
                elements.append(Paragraph(f"\ud83d\uddd3\ufe0f Date: {selected_date}", styles['Normal']))
            if selected_subject:
                try:
                    subject_name = Subject.objects.get(id=selected_subject).name
                    elements.append(Paragraph(f"\ud83d\udcda Subject: {subject_name}", styles['Normal']))
                except:
                    pass
            elements.append(Spacer(1, 12))

            data = [['Student ID', 'Name', 'Subject', 'Status', 'Timestamp']]
            for a in export_data:
                data.append([a['Student ID'], a['Student Name'], a['Subject'], a['Status'], a['Date']])

            table = Table(data, colWidths=[80, 120, 100, 60, 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ]))
            elements.append(table)
            doc.build(elements)

            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response

    context = {
        'attendance_list': unique_attendance,
        'subjects': subjects,
        'selected_date': selected_date,
        'selected_subject': selected_subject,
        'current_lecture': current_lecture,
        'remaining_minutes': remaining_minutes,
    }
    return render(request, 'admin_dashboard.html', context)





# ✅ Create + Show all schedules
def schedule_list_create(request):
    if request.method == "POST":
        subject_id = request.POST.get("subject")
        day = request.POST.get("day_of_week")
        start_time_str = request.POST.get("start_time")  # e.g. "02:00 PM"
        end_time_str = request.POST.get("end_time")      # e.g. "03:30 PM"

        try:
            if subject_id and day and start_time_str and end_time_str:
                subject = Subject.objects.get(id=subject_id)

                # ✅ Parse AM/PM time format
                start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
                end_time = datetime.strptime(end_time_str, "%I:%M %p").time()

                if start_time >= end_time:
                    messages.error(request, "❌ Start time must be before end time.")
                else:
                    LectureSchedule.objects.create(
                        subject=subject,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                    messages.success(request, "✅ Lecture scheduled successfully.")
                    return redirect("/schedule/")
            else:
                messages.error(request, "❌ All fields are required.")

        except ValueError:
            messages.error(request, "❌ Invalid time format. Use HH:MM AM/PM.")
        except Subject.DoesNotExist:
            messages.error(request, "❌ Subject not found.")

    subjects = Subject.objects.all()
    schedules = LectureSchedule.objects.select_related("subject").all()
    return render(request, "schedule.html", {"subjects": subjects, "schedules": schedules})


# ✅ Delete schedule
def delete_schedule(request, pk):
    schedule = get_object_or_404(LectureSchedule, pk=pk)
    schedule.delete()
    messages.success(request, "🗑️ Schedule deleted successfully.")
    return redirect("/schedule/")