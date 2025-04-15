import os
from pynput import keyboard, mouse
 
"""
마우스 / 키보드 잠금을 지원하는 InputBlocker 객체의 설계도 (Class)
 
사용 방법: 객체 생성후 lock_all() / unlock_all() 함수를 사용한다.
ctrl+/ 키로 잠금을 해제한다.
 
"""
 
 
class InputBlocker:
    def __init__(self) -> None:
        #잠금을 해제할 핫키 등록
        self.key_combination = "<ctrl>+/"
        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self.key_combination), self.unlock_and_exit
        )

        #마우스 리스너 
        self.mouse_listener = mouse.Listener(suppress=True)

        #키보드 리스너
        self.keyboard_listener = keyboard.Listener(
            suppress=True,
            on_press=self.for_canonical(self.hotkey.press),
            on_release=self.for_canonical(self.hotkey.release),
        )
 
        # 키보드 / 마우스 잠금 상태
        self.is_keyboard_locked = False
        self.is_mouse_locked = False
 
    def lock_all(self) -> None:
        # 만약 키보드와 마우스 중 하나라도 이미 잠긴 상태로 또 lock을 호출한 경우
        # 2번 lock이 걸리면 무시한다
        if self.is_keyboard_locked or self.is_mouse_locked:
            return
 
        # 키보드와 마우스 모두 잠금
        self.mouse_listener.start()
        self.keyboard_listener.start()
 
        self.is_keyboard_locked = True
        self.is_mouse_locked = True
 
    def show_unblock_message(self):
        print(
            f"키보드 / 마우스 잠금을 해제하고 프로그램을 강제 종료하려면 다음 키 {self.key_combination} 를 누르세요..."
        )
 
    def unlock_all(self) -> None:
        if not self.is_keyboard_locked and not self.is_mouse_locked:
            raise Exception("키보드 / 마우스 잠금이 이미 해제되어 있습니다.")
 
        # 키보드와 마우스 모두 잠금 해제
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        print("키보드 / 마우스 잠금이 해제되었습니다.")
 
        self.is_keyboard_locked = False
        self.is_mouse_locked = False
 
    
    def unlock_and_exit(self) -> None:
        self.unlock_all()
        
        # os._exit(0) 는 모든 쓰레드를 포함하여 즉시 프로세스를 강제 종료한다.
        # 메인 쓰레드, 자식 쓰레드가 남아서 종료되지 않을 수 있는데 전부 죽인다.
        os._exit(0)
 
    #키 입력 표준화
    def for_canonical(self, f):
        return lambda k: f(self.keyboard_listener.canonical(k))
 
 
def main() -> None:
    # 키보드, 마우스 모두 무한정 잠구기
    blocker = InputBlocker()
    blocker.show_unblock_message()
    blocker.lock_all()
 
    while True:
        pass
 

if __name__ == "__main__":
    main()