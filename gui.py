import os
import tkinter as tk
from PIL import Image, ImageTk
import queue

class ShowGui:
    def __init__(self):
        self.root = None
        self.close_request_queue = queue.Queue()
    def show_lock_gui(self):
        self.root = tk.Tk()
        self.root.title("잠금 중")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        image_path = "./lock.png"

        if os.path.exists(image_path):
            image = Image.open(image_path)

            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.ANTIALIAS

            target_width = int(screen_width * 0.8)
            target_height = int(screen_height * 0.8)

            # 원본 이미지 비율 유지하면서 맞추기
            image_ratio = image.width / image.height
            target_ratio = target_width / target_height

            if image_ratio > target_ratio:
                # 이미지가 더 넓음
                resized_width = target_width
                resized_height = int(target_width / image_ratio)
            else:
                # 이미지가 더 높음
                resized_height = target_height
                resized_width = int(target_height * image_ratio)

            image = image.resize((resized_width, resized_height), resample_filter)

            photo = ImageTk.PhotoImage(image)
            img_label = tk.Label(self.root, image=photo, bg="black")
            img_label.image = photo
            img_label.pack(pady=50)
        else:
            print(f"[경고] 이미지 파일 '{image_path}'을(를) 찾을 수 없습니다.")

        label = tk.Label(
            self.root,
            text="입력이 잠금 상태입니다.\n해제하려면 NFC를 태그하세요.",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        label.pack()

        self.check_close_request()

        self.root.mainloop()

    def check_close_request(self):
        try:
            if not self.close_request_queue.empty():
                self.close_request_queue.get_nowait()
                self.root.destroy()
                self.root = None
                return  # 더 이상 mainloop 실행 안 함
        except Exception as e:
            print("GUI 종료 오류:", e)
        self.root.after(100, self.check_close_request)  # 계속 체크
 
    def close_gui(self):
        self.close_request_queue.put(True)
#         if hasattr(self, 'root') and self.root:
#             self.root.destroy()
#             self.root = None


