import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import sqlite3
import io

DB_NAME = "user_enrollment.db"
TABLE_NAME = "users"
RECT_WIDTH, RECT_HEIGHT = 300, 400

# --- Feedback Text States ---
FEEDBACK_STATES = [
    ("Please Blink", (255, 215, 0)),   # Gold
    ("Verified!", (0, 255, 0)),        # Green
    ("Unknown User", (255, 0, 0)),     # Red
]
FEEDBACK_KEYS = {"b": 0, "v": 1, "u": 2}

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image BLOB NOT NULL
    )""")
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
        self.master.title("🎥 Smart Attendance - User Enrollment")
        self.master.configure(bg="#f7f9fc")
        self.master.geometry("700x650")
        self.master.resizable(False, False)

        # --- Style (modern ttk) ---
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12), background="#f7f9fc", foreground="#37474F")
        style.configure("Header.TLabel", font=("Helvetica", 20, "bold"), foreground="#2c3e50")
        style.configure("TButton", font=("Helvetica", 13), padding=6)
        style.map("TButton",
                  background=[("active", "#1976D2")],
                  foreground=[("active", "white")])

        # --- Title ---
        self.title_label = ttk.Label(master, text="Smart Attendance System", style="Header.TLabel")
        self.title_label.pack(pady=12)

        self.subtitle = ttk.Label(master, text="👋 Please look into the camera and enter your name below.")
        self.subtitle.pack(pady=4)

        # --- Entry Section ---
        self.entry_frame = ttk.Frame(master)
        self.entry_frame.pack(pady=10)
        ttk.Label(self.entry_frame, text="Full Name:", font=("Helvetica", 13)).grid(row=0, column=0, padx=5)
        self.name_entry = ttk.Entry(self.entry_frame, font=("Helvetica", 13), width=28)
        self.name_entry.grid(row=0, column=1, padx=5)

        # --- Video Frame Section ---
        self.video_border = tk.Frame(master, bg="#dfe6e9", bd=2, relief="ridge")
        self.video_border.pack(pady=15)
        self.video_frame = tk.Label(self.video_border, bg="#dfe6e9", width=500, height=360)
        self.video_frame.pack()

        # --- Status label under video ---
        self.feedback_label = ttk.Label(master, text="Status: Waiting for input...", font=("Helvetica", 12, "italic"))
        self.feedback_label.pack(pady=6)

        # --- Buttons Section ---
        btn_frame = ttk.Frame(master)
        btn_frame.pack(pady=15)

        self.btn_save = ttk.Button(btn_frame, text="💾 Save Photo", command=self.save_photo)
        self.btn_save.grid(row=0, column=0, padx=15)

        self.btn_quit = ttk.Button(btn_frame, text="❌ Quit", command=self.quit_app)
        self.btn_quit.grid(row=0, column=1, padx=15)

        # Capture Setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "⚠️ Could not access the camera.")
            self.master.destroy()
            return

        self.saved_frame = None
        self.feedback_state = 0  # default: Please Blink
        self.master.bind("<Key>", self.on_key_press)

        self.update_video()

    def on_key_press(self, event):
        key = event.char.lower()
        if key in FEEDBACK_KEYS:
            self.feedback_state = FEEDBACK_KEYS[key]

    def update_video(self):
        ret, frame = self.cap.read()
        if not ret:
            self.video_frame.config(text="Camera not found")
            self.master.after(20, self.update_video)
            return

        h, w = frame.shape[:2]
        left, top = (w - RECT_WIDTH) // 2, (h - RECT_HEIGHT) // 2
        right, bottom = left + RECT_WIDTH, top + RECT_HEIGHT
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 120, 255), 3)

        # Feedback Text On Video
        msg, color_bgr = FEEDBACK_STATES[self.feedback_state]
        cv2.putText(frame, msg, (60, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3,
                    color_bgr, 3, cv2.LINE_AA)
        self.feedback_label.config(text=f"Status: {msg}")

        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2image).resize((500, 360)))
        self.video_frame.imgtk = imgtk
        self.video_frame.config(image=imgtk)

        self.saved_frame = frame.copy()
        self.master.after(20, self.update_video)

    def save_photo(self):
        username = self.name_entry.get().strip()
        if not username:
            messagebox.showwarning("Input Required", "⚠️ Please enter a name before saving.")
            return
        im_pil = Image.fromarray(cv2.cvtColor(self.saved_frame, cv2.COLOR_BGR2RGB))
        with io.BytesIO() as output:
            im_pil.save(output, format="JPEG")
            img_bytes = output.getvalue()
        save_to_database(username, img_bytes)
        messagebox.showinfo("Saved", f"✅ Photo for {username} saved successfully!")

    def quit_app(self):
        if self.cap.isOpened():
            self.cap.release()
        self.master.destroy()


if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = EnrollmentApp(root)
    root.mainloop()
