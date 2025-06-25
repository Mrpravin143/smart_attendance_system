import cv2
import os
import tkinter as tk
from tkinter import messagebox, simpledialog

def manual_face_capture(student_id):
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    dataset_dir = os.path.join(os.path.dirname(__file__), "dataset")
    os.makedirs(dataset_dir, exist_ok=True)

    count = 0
    print(f"\U0001F4F8 Camera started for Student ID {student_id}. Press ESC to stop early.")

    while True:
        ret, img = cam.read()
        if not ret:
            print("\u274C Camera not working.")
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            resized = cv2.resize(face, (200, 200))
            file_path = os.path.join(dataset_dir, f"User.{student_id}.{count+1}.jpg")
            cv2.imwrite(file_path, resized)
            count += 1

            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(img, f"Saved: {count}/30", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow(f"Student {student_id} - Face Capture", img)

        if cv2.waitKey(1) == 27 or count >= 30:
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"\u2705 Saved {count} face images for Student ID {student_id}")
    messagebox.showinfo("Done", f"Saved {count} face images for Student ID {student_id}")

def start_gui():
    root = tk.Tk()
    root.title("Manual Face Capture")
    root.geometry("300x150")

    def capture():
        student_id = entry.get().strip()
        if student_id:
            manual_face_capture(student_id)
        else:
            messagebox.showerror("Error", "Please enter Student ID")

    tk.Label(root, text="Enter Student ID:").pack(pady=10)
    entry = tk.Entry(root)
    entry.pack(pady=5)

    tk.Button(root, text="Start Capture", command=capture).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
