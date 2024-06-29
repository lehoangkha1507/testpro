import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk, Style
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
from exercise import *

model = YOLO("best.pt")

# Đặt thời gian mặc định cho khoảng thời gian làm việc và nghỉ ngơi
WORK_TIME = 25 * 60
SHORT_BREAK_TIME = 5 * 60
LONG_BREAK_TIME = 15 * 60

class PomodoroTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.root.title("Pomodoro Timer")

        # Áp dụng giao diện bằng ttkbootstrap
        self.style = Style(theme="simplex")
        self.style.theme_use()

        # Nhãn hiển thị thời gian
        self.timer_label = ttk.Label(self.root, text="", font=("Helvetica", 40), anchor="center")
        self.timer_label.pack(pady=20)

        # Nút điều khiển
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(pady=10)

        self.start_button = ttk.Button(self.control_frame, text="Bắt đầu", command=self.start_timer, style="success.TButton")
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(self.control_frame, text="Dừng", command=self.stop_timer, state=tk.DISABLED, style="danger.TButton")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Thanh tiến trình
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=10)

        # Khung camera
        self.camera_frame = ttk.Frame(self.root)
        self.camera_frame.pack(pady=20)

        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack()

        # Khởi tạo biến đếm giờ
        self.work_time, self.break_time = WORK_TIME, SHORT_BREAK_TIME
        self.is_work_time, self.pomodoros_completed, self.is_running = True, 0, False

        # Hiển thị thông báo chào mừng
        messagebox.showinfo("Thông báo", "Chào mừng bạn đã quay trở lại với AI Fus và chúc bạn học vui vẻ")

        self.root.mainloop()

    def start_timer(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        self.update_timer()
        self.run_model()

    def run_model(self):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            self.show_frame(frame, cap)
        else:
            messagebox.showerror("Lỗi", "Không thể mở video.")
            self.stop_timer()

    def show_frame(self, frame, cap):
        if self.is_running:
            results = model(frame)

            for result in results:
                boxes = result.boxes  # Đối tượng Boxes cho kết quả hộp giới hạn
                for bbox in boxes.xyxy:
                    xmin, ymin, xmax, ymax = bbox
                    cv2.rectangle(frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 255, 0), 2)
                if len(boxes.xyxy) > 0:
                    if result.names[int(boxes.cls.cpu().numpy()[0])] == 'drowsy':
                        self.stop_timer()
                        messagebox.showerror("Phát hiện buồn ngủ", "Bạn đang buồn ngủ. Hãy nghỉ ngơi!")
                        answer = messagebox.askyesno("Bạn có muốn tập thể dục một chút để tỉnh táo hơn không?")
                        if answer:
                            camera()
                        messagebox.showinfo("Tiếp tục", "Hãy tiếp tục học nào")
                        break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.camera_label.imgtk = imgtk
            self.camera_label.config(image=imgtk)

            if self.is_running and self.is_work_time:
                self.root.after(10, self.show_frame, cap.read()[1], cap)

    def stop_timer(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False

    def update_timer(self):
        if self.is_running:
            if self.is_work_time:
                self.work_time -= 1
                total_time = WORK_TIME
            else:
                self.break_time -= 1
                total_time = LONG_BREAK_TIME if self.pomodoros_completed % 4 == 0 else SHORT_BREAK_TIME

            if self.work_time == 0:
                self.is_work_time = False
                self.pomodoros_completed += 1
                self.break_time = LONG_BREAK_TIME if self.pomodoros_completed % 4 == 0 else SHORT_BREAK_TIME
                message = "Hãy nghỉ dài và thư giãn tâm trí." if self.pomodoros_completed % 4 == 0 else "Hãy nghỉ ngắn và vươn vai!"
                messagebox.showinfo("Thời gian nghỉ", message)

            elif self.break_time == 0:
                self.is_work_time = True
                self.work_time = WORK_TIME
                messagebox.showinfo("Thời gian làm việc", "Hãy làm việc trở lại!")

            current_time = self.work_time if self.is_work_time else self.break_time
            minutes, seconds = divmod(current_time, 60)
            self.timer_label.config(text="{:02d}:{:02d}".format(minutes, seconds))
            self.progress['value'] = (1 - current_time / total_time) * 100

            self.root.after(1000, self.update_timer)

PomodoroTimer()
