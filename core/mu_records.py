"""
core/mu_records.py — MonthlyUpdate ↔ monthly_records resolver
==============================================================
PLAN_ASSET_MODEL §8.5: MU는 월별 요약 앵커, 문서/배정/여행 연결은 monthly_records 정션.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from core.constants import DocType, FileStatus, PatientStatus
from core.models import (
    AssignedHistory,
    Contract,
    DocumentInfo,
    MonthlyRecord,
    MonthlyUpdate,
    Patient,
    Prescription,
    Receipt,
    ReturnReceipt,
    SleepReport,
    TaxInvoice,
    Travel,
)

_TYPED_MODEL_MAP: dict[DocType, type] = {
    DocType.PRESCRIPTION: Prescription,
    DocType.SLEEP_REPORT: SleepReport,
    DocType.CONTRACT: Contract,
    DocType.RETURN_RECEIPT: ReturnReceipt,
    DocType.TAX_INVOICE: TaxInvoice,
    DocType.RECEIPT: Receipt,
}


def add_months(yyyymm: str, delta: int) -> str:
    """YYYY-MM에 delta개월 가감."""
    y, m = int(yyyymm[:4]), int(yyyymm[5:7])
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def month_range(start_yyyymm: str, end_yyyymm: str) -> list[str]:
    """start~end YYYY-MM inclusive."""
    if start_yyyymm > end_yyyymm:
        return []
    months: list[str] = []
    cur = start_yyyymm
    while cur <= end_yyyymm:
        months.append(cur)
        cur = add_months(cur, 1)
    return months


def ensure_mu_for_patient(
    session: Session,
    pat_id: str,
    months: Iterable[str],
) -> list[str]:
    """ACTIVE 환자에 대해 누락 MU 행 생성. SUSPENDED/INACTIVE는 스킵.

    Returns: 새로 생성된 mu_id 목록.
    """
    pat = session.get(Patient, pat_id)
    if not pat:
        return []
    if pat.status == PatientStatus.SUSPENDED:
        return []
    if pat.status == PatientStatus.INACTIVE:
        return []

    created: list[str] = []
    for billing_month in months:
        existing = session.query(MonthlyUpdate).filter_by(
            pat_id=pat_id, billing_month=billing_month,
        ).first()
        if existing:
            continue
        mu = MonthlyUpdate(
            pat_id=pat_id,
            billing_month=billing_month,
            comp_status="PENDING",
            status="PENDING",
        )
        session.add(mu)
        session.flush()
        created.append(mu.mu_id)
    return created


def ensure_mu_new_patient_months(
    session: Session,
    pat_id: str,
    anchor_month: str | None = None,
) -> list[str]:
    """신규 환자: anchor_month ~ anchor+3 MU ensure (PLAN §4.3)."""
    if anchor_month is None:
        anchor_month = datetime.now().strftime("%Y-%m")
    end = add_months(anchor_month, 3)
    return ensure_mu_for_patient(session, pat_id, month_range(anchor_month, end))


def ensure_mu_login_grid(session: Session, last_login_at: datetime | None) -> int:
    """관리자 로그인 시 ACTIVE 환자 MU 그리드 ensure (PLAN §4.2).

    start = (last_login_month + 1) or current_month
    end   = current_month + 3
    Returns: 생성된 MU 행 수.
    """
    current_month = datetime.now().strftime("%Y-%m")
    if last_login_at:
        start = add_months(last_login_at.strftime("%Y-%m"), 1)
    else:
        start = current_month
    end = add_months(current_month, 3)
    if start > end:
        return 0

    months = month_range(start, end)
    total = 0
    active_ids = [
        row[0]
        for row in session.query(Patient.pat_id)
        .filter(Patient.status == PatientStatus.ACTIVE)
        .all()
    ]
    for pat_id in active_ids:
        total += len(ensure_mu_for_patient(session, pat_id, months))
    return total


def get_or_create_mu(session: Session, pat_id: str, billing_month: str) -> MonthlyUpdate:
    mu = session.query(MonthlyUpdate).filter_by(
        pat_id=pat_id, billing_month=billing_month,
    ).first()
    if mu:
        return mu
    mu = MonthlyUpdate(
        pat_id=pat_id,
        billing_month=billing_month,
        comp_status="PENDING",
        status="PENDING",
    )
    session.add(mu)
    session.flush()
    return mu


def link_mu_doc(session: Session, mu_id: str, doc_id: str) -> MonthlyRecord:
    existing = session.query(MonthlyRecord).filter_by(mu_id=mu_id, doc_id=doc_id).first()
    if existing:
        return existing
    rec = MonthlyRecord(mu_id=mu_id, doc_id=doc_id)
    session.add(rec)
    session.flush()
    return rec


def link_mu_assignment(session: Session, mu_id: str, assigned_history_id: str) -> MonthlyRecord:
    existing = session.query(MonthlyRecord).filter_by(
        mu_id=mu_id, assigned_history_id=assigned_history_id,
    ).first()
    if existing:
        return existing
    rec = MonthlyRecord(mu_id=mu_id, assigned_history_id=assigned_history_id)
    session.add(rec)
    session.flush()
    return rec


def link_mu_travel(session: Session, mu_id: str, travel_id: str) -> MonthlyRecord:
    existing = session.query(MonthlyRecord).filter_by(mu_id=mu_id, travel_id=travel_id).first()
    if existing:
        return existing
    rec = MonthlyRecord(mu_id=mu_id, travel_id=travel_id)
    session.add(rec)
    session.flush()
    return rec


def _doc_ids_for_mu(session: Session, mu_id: str, doc_type: DocType) -> list[str]:
    rows = (
        session.query(MonthlyRecord.doc_id)
        .join(DocumentInfo, MonthlyRecord.doc_id == DocumentInfo.doc_id)
        .filter(
            MonthlyRecord.mu_id == mu_id,
            DocumentInfo.doc_type == doc_type.value,
        )
        .all()
    )
    return [row[0] for row in rows if row[0]]


def get_typed_docs_for_mu(session: Session, mu_id: str, doc_type: DocType) -> list:
    model = _TYPED_MODEL_MAP.get(doc_type)
    if model is None:
        return []
    doc_ids = _doc_ids_for_mu(session, mu_id, doc_type)
    if not doc_ids:
        return []
    return session.query(model).filter(model.doc_id.in_(doc_ids)).all()


def get_typed_doc_for_mu(session: Session, mu_id: str, doc_type: DocType):
    docs = get_typed_docs_for_mu(session, mu_id, doc_type)
    if not docs:
        return None
    if doc_type == DocType.PRESCRIPTION:
        active = [d for d in docs if d.superseded_by_ps_id is None]
        pool = active if active else docs
        return max(pool, key=lambda d: d.issue_date or d.start_date or datetime.min)
    if doc_type == DocType.RETURN_RECEIPT:
        return max(docs, key=lambda d: d.return_date or datetime.min)
    if doc_type == DocType.TAX_INVOICE:
        return max(docs, key=lambda d: d.ti_issue_date or datetime.min)
    if doc_type == DocType.RECEIPT:
        return max(docs, key=lambda d: d.rcpt_issue_date or datetime.min)
    return docs[0]


def mu_has_doc_type(session: Session, mu_id: str, doc_type: DocType) -> bool:
    return bool(_doc_ids_for_mu(session, mu_id, doc_type))


def is_typed_record_linked_any_mu(session: Session, doc_id: str | None) -> bool:
    if not doc_id:
        return False
    return session.query(MonthlyRecord).filter_by(doc_id=doc_id).first() is not None


def create_excel_stub_document(
    session: Session,
    pat_id: str,
    doc_type: DocType,
    issue_date: str,
) -> DocumentInfo:
    """Excel TX/RC용 stub patient_documents (파일 없음, OCR pending 제외)."""
    stub = DocumentInfo(
        pat_id=pat_id,
        doc_type=doc_type,
        directory=None,
        generated_filename=None,
        issue_date=issue_date,
        file_status=FileStatus.EXCEL,
    )
    session.add(stub)
    session.flush()
    return stub


def link_tax_invoice_to_mu(
    session: Session,
    mu: MonthlyUpdate,
    ti: TaxInvoice,
    issue_date: str,
) -> None:
    if ti.doc_id is None:
        stub = create_excel_stub_document(
            session,
            ti.pat_id,
            DocType.TAX_INVOICE,
            issue_date[:7] if issue_date else mu.billing_month,
        )
        ti.doc_id = stub.doc_id
    link_mu_doc(session, mu.mu_id, ti.doc_id)


def link_receipt_to_mu(
    session: Session,
    mu: MonthlyUpdate,
    rc: Receipt,
    issue_date: str,
) -> None:
    if rc.doc_id is None:
        stub = create_excel_stub_document(
            session,
            rc.pat_id,
            DocType.RECEIPT,
            issue_date[:7] if issue_date else mu.billing_month,
        )
        rc.doc_id = stub.doc_id
    link_mu_doc(session, mu.mu_id, rc.doc_id)
