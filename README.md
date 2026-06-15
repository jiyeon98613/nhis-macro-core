# nhis-macro-core

인케어랩 CPAP 건강보험 청구 자동화 시스템의 **공유 코어 라이브러리**입니다.  
SQLAlchemy ORM, 듀얼 SQLite 매니저, 워크플로우 프레임워크, 인증·감사 레이어를 제공하며,  
실행 엔진(`nhis-macro-engine`)과 병원별 설정(`nhis-macro-config`)이 이 패키지를 import 합니다.

---

## 역할

| 레이어 | 저장소 | 역할 |
|--------|--------|------|
| **Core** (본 저장소) | `nhis-macro-core` | DB 모델, 세션 매니저, 워크플로우, Alembic |
| **Engine** | `nhis-macro-engine` | FastAPI, OCR, 청구 계산, RPA, CLI 데모 |
| **Config** | `nhis-macro-config` | `config.yaml`, DB 파일 경로 |

운영 진입점은 `nhis-macro-engine/api/main.py`(FastAPI)이며, 본 저장소는 라이브러리로만 사용됩니다.

---

## DB 구조

SQLite **2개**를 분리 운영합니다. 절대 혼용하지 않습니다.

| DB | Base | 용도 | 주요 테이블 |
|----|------|------|-------------|
| `onboarding.db` | `OnboardingBase` | 기준정보 | `vendors`, `operators`, `document_templates`, `frequent_hospitals`, … |
| `runtime.db` | `RuntimeBase` | 운영정보 | `patients`, `prescriptions`, `sleep_reports`, `claims`, `ocr_sessions`, … |

- **PK/FK**: `String(36)` UUID (`str(uuid.uuid4())`)
- **멀티테넌시**: 전 테이블 `org_id` (기본값은 `core.org_context`에서 config 주입)
- **감사/소프트 삭제**: `updated_at`, `created_by`, `updated_by`, `deleted_at`
- **스키마 SSoT**: `core/models.py` — 변경 시 `docs/db-schema.html`(루트 `nhis-macro/`)도 함께 갱신

참조용 DDL: [`sql/schema.sql`](sql/schema.sql) (onboarding + runtime 전체).  
실제 마이그레이션은 Alembic이 권위를 가집니다.

```bash
# onboarding.db
alembic -x db=onboarding upgrade head

# runtime.db
alembic -x db=runtime upgrade head
```

개발용 전체 재생성(테스트 DB만): `nhis-macro-engine/scripts/setup/recreate_db.py`

---

## 디렉터리 구조

```text
nhis-macro-core/
├── core/
│   ├── models.py           # ORM 모델 (OnboardingBase / RuntimeBase)
│   ├── db_manager.py       # 듀얼 DB 싱글턴 `db`
│   ├── org_context.py      # org_id 기본값 주입
│   ├── auth.py / auth_manager.py / security.py
│   ├── audit_listener.py   # 민감 테이블 → AuditLog 자동 기록
│   ├── constants.py
│   └── workflow/           # BaseStep, WorkflowRunner, StateMachine
├── alembic/                # -x db=onboarding | runtime
├── sql/
│   └── schema.sql          # models.py 기준 참조 DDL
└── tests/
```

---

## 세션 사용법

```python
from core.db_manager import db

db.initialize(onboarding_path, runtime_path)

session = db.get_runtime_session()
try:
    # ORM 작업
    session.commit()
finally:
    session.close()
```

- onboarding 세션: `db.get_onboarding_session()`
- runtime 세션: `db.get_runtime_session()`
- 감사 이벤트: `db.log_event()` 또는 `audit_listener` 자동 기록

---

## 워크플로우

모든 Step은 `core.workflow.base_step.BaseStep`을 상속하고 `run(context) -> dict | None`을 구현합니다.

```text
LOAD_INPUT → PRE_VALIDATE → USER_CONFIRM → AUTO_INPUT → SAVE_ONLY → RESULT_LOG
```

`SAVE_ONLY`까지가 자동화 범위이며, 최종 제출(SUBMIT)은 사용자 또는 별도 매크로가 담당합니다.

---

## 개인정보·보안 원칙

- **주민번호 원본 저장 금지** — `reg_num_front` / `reg_num_back` 분리 저장만 허용
- 민감 테이블 변경은 `audit_logs`에 기록
- OCR 외부 API 전송 전 PII 마스킹은 engine 레이어(`pii_masker`)에서 처리
- cross-DB 참조(`operators`, `frequent_hospitals` ↔ runtime)는 FK 없이 `String(36)` soft ref

---

## 테스트

```bash
cd nhis-macro-core
pytest tests/
```

DB 의존 테스트는 in-memory SQLite 또는 `tmp_path` fixture를 사용합니다.

---

## 관련 문서

루트 `nhis-macro/` 저장소:

- [`PRODUCT.md`](../PRODUCT.md) — 비즈니스 규칙·진행 상태 SSoT
- [`docs/db-schema.html`](../docs/db-schema.html) — ERD 시각화

---

## 라이선스

MIT License — 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.

본 소프트웨어는 어떠한 보증도 제공하지 않으며, 건강보험 청구 결과에 대한 책임은 사용자에게 있습니다.
