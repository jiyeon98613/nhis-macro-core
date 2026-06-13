"""
core/org_context.py — 기본 org_id(tenant) 컨텍스트
====================================================
설치형→중앙형 §12 원칙①. OrgMixin.org_id 기본값의 단일 소스.

core는 engine/config 계층에 의존하면 안 되므로(순환참조), 여기서는
안전한 fallback("inkair-lab")만 들고, 실제 값은 앱 시작 시점에
engine 쪽(env_setup.get_org_id())이 set_default_org_id()로 주입한다.

주입 시점: api/main.py, scripts/setup/recreate_db.py 등 부트스트랩 단계.
주입 전에는 fallback 이 적용된다(테스트·단독 실행 호환).
"""

_DEFAULT_ORG_ID = "inkair-lab"


def set_default_org_id(org_id: str) -> None:
    """OrgMixin.org_id 기본값을 주입. 빈 값이면 무시(기존 fallback 유지)."""
    global _DEFAULT_ORG_ID
    if org_id:
        _DEFAULT_ORG_ID = org_id


def get_default_org_id() -> str:
    return _DEFAULT_ORG_ID
