import cv2
import numpy as np
from PIL import Image
import os
import re
import tkinter as tk
from tkinter import messagebox

def train_model():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    path = os.path.join(os.path.dirname(__file__), 'dataset')

    def get_images_and_labels(path):
        face_samples = []
        ids = []
        for filename in os.listdir(path):
            if filename.lower().endswith(('jpg', 'png')):
                match = re.match(r"User\.(\d+)\.\d+\.(jpg|png)", filename, re.IGNORECASE)
                if not match:
                    continue
                id = int(match.group(1))
                img_path = os.path.join(path, filename)
                gray_img = Image.open(img_path).convert('L')
                img_np = np.array(gray_img, 'uint8')
                faces = detector.detectMultiScale(img_np)
                for (x, y, w, h) in faces:
                    face_samples.append(img_np[y:y+h, x:x+w])
                    ids.append(id)
        return face_samples, ids

    print("Training started...")
    faces, ids = get_images_and_labels(path)
    if not faces:
        print("No faces found.")
        messagebox.showerror("Error", "No faces found in dataset!")
        return

    recognizer.train(faces, np.array(ids))
    recognizer.save(os.path.join(os.path.dirname(__file__), 'trainer.yml'))
    print("Model saved as trainer.yml")
    messagebox.showinfo("Success", "Model trained and saved as trainer.yml")

def start_training_gui():
    window = tk.Tk()
    window.title("Train Face Recognition Model")
    window.geometry("300x150")

    tk.Label(window, text="Click to Train Model", font=("Arial", 12)).pack(pady=20)
    tk.Button(window, text="Start Training", command=train_model).pack(pady=10)

    window.mainloop()

if __name__ == "__main__":
    start_training_gui()
