import winreg
import ctypes
import sys
import os

class USBBlocker:
    REG_PATH = r"SYSTEM\CurrentControlSet\Services\USBSTOR"

    def __init__(self):
        self.original_value = None

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def set_usb_state(self, enable: bool):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                self.original_value, _ = winreg.QueryValueEx(key, "Start")

                new_value = 3 if enable else 4
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, new_value)

                print(f"USB {'활성화' if enable else '비활성화'} 완료.")
        except PermissionError:
            print("레지스트리 접근 권한이 없습니다. 관리자 권한으로 실행해야 합니다.")
            sys.exit(1)

    def restore_original(self):
        if self.original_value is not None:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.REG_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, self.original_value)
            print("원래 USB 설정으로 복구 완료.")

# 관리자 권한으로 다시 실행
def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("관리자 권한으로 다시 실행 중...")
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

if __name__ == "__main__":
    run_as_admin()

    usb_blocker = USBBlocker()
    usb_blocker.set_usb_state(False)  # USB 비활성화

    try:
        import time
        print("USB 차단 상태입니다. 10초 대기 중...")
        time.sleep(10)
    finally:
        usb_blocker.restore_original()  # 종료 시 원상복구
