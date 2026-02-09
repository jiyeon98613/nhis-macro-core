from core.db_manager import db, HOSP_CONFIG
from core.models import Hospital
from core.security import get_hwid

def validate_license():
    session = db.get_session()
    current_hwid = get_hwid()
    conf_code = str(HOSP_CONFIG['target_code'])

    hosp = session.query(Hospital).filter(Hospital.hosp_code == conf_code).first()

    if not hosp:
        print("❌ 인증 에러: 등록되지 않은 병원 코드입니다.")
        return False

    if hosp.device_hwid != current_hwid:
        print("🛑 보안 경고: 인증되지 않은 기기에서 실행되었습니다. (불법 복제 의심)")
        print(f"등록된 기기: {hosp.device_hwid} / 현재 기기: {current_hwid}")
        return False

    print(f"✅ 기기 인증 완료: {hosp.hosp_name} 전용 모드 가동")
    return True