import os
import threading
import tkinter as tk
from pynput import keyboard, mouse
from PIL import Image, ImageTk

class InputBlocker:
    def __init__(self) -> None:
        self.key_combination = "<ctrl>+/"
        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self.key_combination), self.unlock_and_exit
        )

        self.mouse_listener = mouse.Listener(suppress=True)
        self.keyboard_listener = keyboard.Listener(
            suppress=True,
            on_press=self.for_canonical(self.hotkey.press),
            on_release=self.for_canonical(self.hotkey.release),
        )

        self.is_keyboard_locked = False
        self.is_mouse_locked = False

        # GUI 관련
        self.gui_thread = None
        self.root = None

    def lock_all(self) -> None:
        if self.is_keyboard_locked or self.is_mouse_locked:
            return

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.is_keyboard_locked = True
        self.is_mouse_locked = True

        # GUI 띄우기 (별도 쓰레드에서 실행)
        self.gui_thread = threading.Thread(target=self.show_lock_gui)
        self.gui_thread.daemon = True
        self.gui_thread.start()

    def unlock_all(self) -> bool:
        if not self.is_keyboard_locked and not self.is_mouse_locked:
            return False

        self.mouse_listener.stop()
        self.keyboard_listener.stop()

        self.is_keyboard_locked = False
        self.is_mouse_locked = False

        # GUI 닫기
        if self.root:
            self.root.quit()

        print("키보드 / 마우스 잠금이 해제되었습니다.")
        return True

    def unlock_and_exit(self) -> None:
        self.unlock_all()
        os._exit(0)

    def for_canonical(self, f):
        return lambda k: f(self.keyboard_listener.canonical(k))

    def show_lock_gui(self):
        self.root = tk.Tk()
        self.root.title("잠금 중")
        self.root.attributes("-fullscreen", True)  # 전체 화면
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")  # 배경색

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # 닫기 버튼 비활성화

        # 이미지 경로 설정
        image_path = "lock.jpg"  # 실행 파일과 동일 경로에 있어야 함

        # 이미지 로딩 및 라벨로 표시
        if os.path.exists(image_path):
            image = Image.open(image_path)
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.ANTIALIAS  # Pillow < 10.0 대응

            image = image.resize((1300, 800), resample_filter)

            photo = ImageTk.PhotoImage(image)
            img_label = tk.Label(self.root, image=photo, bg="black")
            img_label.image = photo  # 참조 유지
            img_label.pack(pady=50)
        else:
            print(f"[경고] 이미지 파일 '{image_path}'을(를) 찾을 수 없습니다.")

        # 텍스트 라벨
        label = tk.Label(
            self.root,
            text="입력이 잠금 상태입니다.\nCtrl+/ 키로 해제하세요.",
            font=("Arial", 24),
            fg="white",
            bg="black"
        )
        label.pack()

        self.root.mainloop()



def main() -> None:
    blocker = InputBlocker()
    blocker.lock_all()

    # 무한 루프 대신 CPU 점유율이 낮은 방식으로 대기
    threading.Event().wait()


if __name__ == "__main__":
    main()
