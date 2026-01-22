#모든 단계가 따라야하는 형식
# 자동화/검증/저장 여부와 무관
from abc import ABC, abstractmethod

class BaseStep(ABC):
    @abstractmethod
    def run(self, context: dict) -> None:
        pass
