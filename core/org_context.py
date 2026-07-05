"""
core/org_context.py — 기본 org_id(tenant) 컨텍스트
====================================================
설치형→중앙형 §12 원칙①. OrgMixin.org_id 기본값의 단일 소스.

core는 engine/config 계층에 의존하면 안 되므로(순환참조), 여기서는
config [org.id] 미설정 시에만 쓰는 fallback("incare-lab")을 둔다.
실제 값은 bootstrap/seed/FastAPI 시작 시 env_setup.apply_org_from_config()가 주입.

    apply_org_from_config() 호출처:
    - nhis-macro-engine/env_setup.py          get_org_id() + apply_org_from_config()
    - nhis-macro-engine/api/main.py           FastAPI 기동
    - nhis-macro-engine/scripts/setup/recreate_db.py
    - nhis-macro-engine/scripts/setup/seed_master.py
"""

_DEFAULT_ORG_ID = "incare-lab"


def set_default_org_id(org_id: str) -> None:
    """OrgMixin.org_id 기본값을 주입. 빈 값이면 무시(기존 fallback 유지)."""
    global _DEFAULT_ORG_ID
    if org_id:
        _DEFAULT_ORG_ID = org_id


def get_default_org_id() -> str:
    return _DEFAULT_ORG_ID
