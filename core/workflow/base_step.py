# core/workflow/base_step.py

from abc import ABC, abstractmethod

class BaseStep(ABC):
    @property
    def name(self):
        """스텝의 이름을 클래스명으로 자동 설정"""
        return self.__class__.__name__

    @abstractmethod
    def run(self, context: dict) -> None:
        """모든 스텝이 공통으로 구현해야 하는 실행 로직"""
        pass

    def log(self, message: str):
        """통일된 로그 출력 형식"""
        print(f"🔹 [{self.name}] {message}")

    def handle_failure(self, error):
        """에러 발생 시 사용자로부터 후속 조치를 입력받음"""
        print(f"\n❌ [{self.name}] 실행 중 오류가 발생했습니다.")
        print(f"📝 상세 에러: {error}")
        
        while True:
            choice = input("👉 작업 선택 (r: 재시도, s: 건너뛰기, q: 전체 종료): ").lower().strip()
            if choice in ['r', 's', 'q']:
                return choice
            print("❗ 잘못된 입력입니다. r, s, q 중 하나를 입력하세요.")