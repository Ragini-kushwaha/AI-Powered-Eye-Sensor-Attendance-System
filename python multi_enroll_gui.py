import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import sqlite3
import io

DB_NAME = "user_enrollment.db"
TABLE_NAME = "users"
RECT_WIDTH, RECT_HEIGHT = 300, 400

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_to_database(username, image_bytes):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"INSERT INTO {TABLE_NAME} (name, image) VALUES (?, ?)", (username, image_bytes))
    conn.commit()
    conn.close()

class EnrollmentApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Smart Attendance System")
        self.master.configure(bg='#ECEFF1')
        self.master.resizable(False, False)

        self.label_title = tk.Label(
            master, text="User Enrollment – Please Look at the Camera", font=('Helvetica', 18, 'bold'),
            bg='#ECEFF1', fg='#37474F')
        self.label_title.pack(pady=10)

        self.entry_frame = tk.Frame(master, bg='#ECEFF1')
        self.entry_frame.pack(pady=5)
        tk.Label(self.entry_frame, text="Name:", font=('Helvetica', 12), bg='#ECEFF1').pack(side=tk.LEFT)
        self.name_entry = tk.Entry(self.entry_frame, font=('Helvetica', 12), width=20)
        self.name_entry.pack(side=tk.LEFT)

        self.video_frame = tk.Label(master, bg='#B0BEC5')
        self.video_frame.pack(padx=20, pady=10)

        button_frame = tk.Frame(master, bg='#ECEFF1')
        button_frame.pack(pady=5)
        self.btn_save = tk.Button(
            button_frame, text="Save Photo", font=('Helvetica', 14),
            command=self.save_photo, bg='#03A9F4', fg='white', width=15)
        self.btn_save.pack(side=tk.LEFT, padx=10)

        self.btn_quit = tk.Button(
            button_frame, text="Quit", font=('Helvetica', 14),
            command=self.quit_app, bg='#B71C1C', fg='white', width=10)
        self.btn_quit.pack(side=tk.LEFT, padx=10)

        self.cap = cv2.VideoCapture(0)
        self.saved_frame = None
        self.update_video()

    def update_video(self):
        ret, frame = self.cap.read()
        if not ret:
            self.video_frame.config(text='Failed to grab frame')
            return

        h, w = frame.shape[:2]
        left = (w - RECT_WIDTH) // 2
        top = (h - RECT_HEIGHT) // 2
        right = left + RECT_WIDTH
        bottom = top + RECT_HEIGHT
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 120, 255), 3)

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(cv2image)
        im_pil = im_pil.resize((450, 340))
        self.imgtk = ImageTk.PhotoImage(image=im_pil)
        self.video_frame.config(image=self.imgtk)
        self.video_frame.image = self.imgtk
        self.saved_frame = frame.copy()
        self.master.after(15, self.update_video)

    def save_photo(self):
        username = self.name_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a name before saving.")
            return

        # Crop to the face rectangle (optional: here we just save the whole frame, you can crop if you want).
        im_pil = Image.fromarray(cv2.cvtColor(self.saved_frame, cv2.COLOR_BGR2RGB))
        with io.BytesIO() as output:
            im_pil.save(output, format="JPEG")
            image_bytes = output.getvalue()

        save_to_database(username, image_bytes)
        messagebox.showinfo("Saved", f"Photo for {username} saved to database.")

    def quit_app(self):
        self.cap.release()
        self.master.destroy()

if __name__ == '__main__':
    setup_database()
    root = tk.Tk()
    app = EnrollmentApp(root)
    root.mainloop()
