# nhis-macro-core/workflow/base_step.py

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