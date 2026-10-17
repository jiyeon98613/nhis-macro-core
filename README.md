# nhis-macro-core · 초기 SQLite MVP 스냅샷

이 저장소는 건강보험 청구 자동화 프로젝트의 **초기 SQLite 기반 공유 코어 라이브러리**를 보존한 공개 스냅샷입니다. 현재 PostgreSQL 기반 운영 시스템 전체를 나타내는 저장소는 아닙니다.

현재 프로젝트의 설계와 담당 범위:

- [건강보험 청구 시스템 — 문서 상태·청구 근거·OCR 개선](https://jiyeon98613.github.io/projects/nhis-billing/)
- [관리자 콘솔 — 실제 UI와 DB·백엔드 기여](https://jiyeon98613.github.io/projects/admin-console/)
- [포트폴리오 홈](https://jiyeon98613.github.io/)

## 이 스냅샷에 있는 것

| 영역 | 당시 구조 |
| --- | --- |
| DB 모델 | 환자·처방·기기·청구 관련 SQLAlchemy 모델 |
| DB 연결 | onboarding.db / runtime.db로 분리한 듀얼 SQLite 매니저 |
| 공통 기능 | 인증·감사 기록·워크플로우 프레임워크 |
| 변경 이력 | 당시 SQLite 구조에 대한 Alembic migration |

DB 모델의 String UUID, org_id와 두 DB 연결 방식은 이 시기의 구현입니다. 현재의 PostgreSQL native UUID·업체 범위·DB 권한 계약과 구분해서 읽어 주세요.

## 프로젝트의 변화

1. 청구 업무의 요구사항을 정리하고 SQLite 기반 MVP 개발
2. 2026년 7월 PostgreSQL 기반으로 전환
3. DB·백엔드·배치를 고도화하고 관리자 웹으로 청구 기능 통합 진행

현재 시스템의 구현 소스와 운영 데이터는 이 공개 스냅샷에 추가하지 않습니다. 공개 가능한 설계 관계·가상 사례·기여 범위는 포트폴리오에 정리합니다.

## 코드 탐색

- [core/models.py](core/models.py): 당시 데이터 모델
- [core/db_manager.py](core/db_manager.py): 듀얼 DB 연결과 세션 관리
- [core/workflow](core/workflow): 공통 워크플로우
- [alembic/versions](alembic/versions): 당시 스키마 변경 이력
- [tests](tests): 당시 구조에 대한 테스트

## 라이선스

기존 [MIT License](LICENSE)를 따릅니다.
