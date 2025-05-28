# requirements: pynput, Pillow
import sys
import os
import threading
from pynput import keyboard, mouse
from gui import ShowGui
import usb
import asyncio
import queue
import Netlink
import time

class InputBlocker:
    def __init__(self,control_queue: queue.Queue) -> None:
        self.control_queue = control_queue  # 큐 주입

        self.key_combination = "<ctrl>+/"

        self.mouse_listener = None
        self.keyboard_listener = None

        self.is_keyboard_locked = False
        self.is_mouse_locked = False

        # GUI 관련
        self.gui_thread = None
        self.gui_instance = ShowGui()

        #usb 관련
        self.usb_blocker = usb.USBBlocker()

    def _on_key_press(self, key):
        try:
            self.hotkey.press(self.keyboard_listener.canonical(key))
        except Exception as e:
            print("핫키 press 오류:", e)

    def _on_key_release(self, key):
        try:
            self.hotkey.release(self.keyboard_listener.canonical(key))
        except Exception as e:
            print("핫키 release 오류:", e)

    def lock_all(self) -> None:
        if self.is_keyboard_locked or self.is_mouse_locked:
            return

        if not self.mouse_listener or not self.mouse_listener.is_alive():
            self.mouse_listener = mouse.Listener(suppress=True)
            self.mouse_listener.daemon = True
            self.mouse_listener.start()

        if not self.keyboard_listener or not self.keyboard_listener.is_alive():
            # 핫키 입력 시 키보드 마우스 잠금만 해제하는 코드
            self.hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(self.key_combination), self.unlock_all
            )
            # 핫키 입력 시 프로그램을 강제 종료하는 코드
#             self.hotkey = keyboard.HotKey(
#                 keyboard.HotKey.parse(self.key_combination), self.unlock_and_exit
#             )
            self.keyboard_listener = keyboard.Listener(
                suppress=True,
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()

        self.is_keyboard_locked = True
        self.is_mouse_locked = True

        if hasattr(self.usb_blocker, 'set_usb_state'):
                    self.usb_blocker.set_usb_state(False)

        if not self.gui_thread or not self.gui_thread.is_alive():
            self.gui_thread = threading.Thread(target=self.gui_instance.show_lock_gui)
            self.gui_thread.daemon = True
            self.gui_thread.start()

    def unlock_all(self) -> bool:
        if not self.is_keyboard_locked and not self.is_mouse_locked:
            return False

        if self.mouse_listener and self.mouse_listener.running:
            self.mouse_listener.stop()

        if self.keyboard_listener and self.keyboard_listener.running:
            self.keyboard_listener.stop()

        self.is_keyboard_locked = False
        self.is_mouse_locked = False

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

def run_network(control_queue):
    print("연결 시도중...")
    asyncio.run(Netlink.network_start("com", "70-85-C2-C1-6D-28", "11-11-11-11-11-11", control_queue))

def main() -> None:
    usb.run_as_admin()

    control_queue = queue.Queue(maxsize=4)

    # network_start 백그라운드에서 실행
    network_thread = threading.Thread(target=run_network,args=(control_queue,))
    network_thread.daemon = True
    network_thread.start()

    blocker = InputBlocker(control_queue)
    blocker.lock_all()

 # 주기적으로 큐 상태를 확인하여 lock/unlock 수행
    while True:
        if control_queue.empty():
            blocker.lock_all()
        else:
            blocker.unlock_all()
        # sleep하는 시간으로 큐가 비어있는지 감시하는 빈도를 조절
        time.sleep(7)

if __name__ == "__main__":
    main()
