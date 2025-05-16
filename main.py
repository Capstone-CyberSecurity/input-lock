import os
import threading
from pynput import keyboard, mouse
from gui import ShowGui
import usb

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
        self.gui_instance = ShowGui()
        self.root = None

        #usb 관련
        self.usb_blocker = usb.USBBlocker()
        


    def lock_all(self) -> None:
        if self.is_keyboard_locked or self.is_mouse_locked:
            return

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.is_keyboard_locked = True
        self.is_mouse_locked = True

        self.usb_blocker.set_usb_state(False)

        # GUI 띄우기 (별도 쓰레드에서 실행)
        self.gui_thread = threading.Thread(target=self.gui_instance.show_lock_gui)
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
        if hasattr(self, 'gui_instance'):
            self.gui_instance.close_gui()

        if hasattr(self, 'usb_blocker'):
            self.usb_blocker.restore_original()

        print("키보드 / 마우스 잠금이 해제되었습니다.")
        return True

    def unlock_and_exit(self) -> None:
        self.unlock_all()
        os._exit(0)

    def for_canonical(self, f):
        return lambda k: f(self.keyboard_listener.canonical(k))

def main() -> None:
    usb.run_as_admin()

    blocker = InputBlocker()
    blocker.lock_all()

    # 무한 루프 대신 CPU 점유율이 낮은 방식으로 대기
    threading.Event().wait()


if __name__ == "__main__":
    main()
