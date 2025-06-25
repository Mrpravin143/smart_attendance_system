import cv2
import os
import sys
import django
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
import pyttsx3

# ✅ Django Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_attendance.settings")
django.setup()

from attendance.models import Student, Attendance, Subject, LectureSchedule

# 🔊 Voice Feedback
def speak_once(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# ✅ Get current lecture
def get_current_lecture_subject():
    now = datetime.now().time()
    day = datetime.now().strftime('%A')
    lecture = LectureSchedule.objects.filter(
        day_of_week=day,
        start_time__lte=now,
        end_time__gte=now
    ).select_related('subject').first()
    return lecture

# ✅ Get student by ID
def get_student_by_id(student_id):
    try:
        return Student.objects.get(student_id=str(student_id))
    except Student.DoesNotExist:
        return None

# ✅ Mark attendance (Present)
def mark_attendance(student, subject):
    today = timezone.now().date()
    try:
        att = Attendance.objects.get(
            student=student,
            subject=subject,
            timestamp__date=today
        )
        if att.status != "Present":
            att.status = "Present"
            att.timestamp = timezone.now()
            att.save()
            speak_once(f"{student.name}, your attendance has been marked successfully.")
            return "Marked"
        else:
            speak_once(f"{student.name}, your attendance for {subject.name} is already marked.")
            return "Already"
    except Attendance.DoesNotExist:
        Attendance.objects.create(
            student=student,
            subject=subject,
            status="Present",
            timestamp=timezone.now()
        )
        speak_once(f"{student.name}, your attendance has been marked successfully.")
        return "Created"

# ✅ Mark Absent for students not detected
def mark_absent_for_non_detected_students(detected_student_ids, subject):
    today = timezone.now().date()
    all_students = Student.objects.all()

    for student in all_students:
        if str(student.student_id) not in detected_student_ids:
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

# ✅ Main Recognition Logic
def recognize_and_mark():
    lecture = get_current_lecture_subject()
    if not lecture:
        speak_once("No lecture is currently active.")
        print("❌ No current lecture.")
        return

    subject = lecture.subject
    end_time = lecture.end_time
    end_timestamp = datetime.combine(datetime.today(), end_time)

    print(f"📚 Current Subject: {subject.name}")
    print(f"⏰ Lecture ends at: {end_time}")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    today_str = datetime.today().strftime("%Y-%m-%d")

    already_announced_ids = set()

    while True:
        if datetime.now() >= end_timestamp:
            print("🔔 Lecture time over. Stopping recognition...")
            break

        ret, img = cam.read()
        if not ret:
            print("Camera error.")
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            name = "Unknown"

            if confidence < 50:
                student = get_student_by_id(id_)
                if student:
                    if id_ not in already_announced_ids:
                        result = mark_attendance(student, subject)
                        already_announced_ids.add(id_)
                    name = student.name
                else:
                    if "unknown" not in already_announced_ids:
                        speak_once("Sorry. Unknown person.")
                        already_announced_ids.add("unknown")
            else:
                if "unknown" not in already_announced_ids:
                    speak_once("Sorry. Unknown person.")
                    already_announced_ids.add("unknown")

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, name, (x, y - 10), font, 0.7, (0, 255, 0), 2)

        # Display Subject & Date
        cv2.putText(img, f"Subject: {subject.name}", (20, 30), font, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Date: {today_str}", (20, 60), font, 0.7, (255, 255, 255), 2)

        cv2.imshow("📸 Attendance", img)
        if cv2.waitKey(1) == 27:  # ESC to exit
            break

    cam.release()
    cv2.destroyAllWindows()

    # ✅ Convert present IDs to string for comparison
    detected_ids = [str(i) for i in already_announced_ids if isinstance(i, int)]

    # ✅ Mark Absent for rest of students
    mark_absent_for_non_detected_students(detected_student_ids=detected_ids, subject=subject)

if __name__ == "__main__":
    recognize_and_mark()
