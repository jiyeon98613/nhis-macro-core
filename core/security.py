# core/security.py
"""
core/security.py — 암호화·해싱·하드웨어 식별
=============================================
1. SecurityManager: Fernet 대칭키 암호화/복호화 (config, 주민번호 뒷자리)
2. get_hwid(): 윈도우 메인보드 시리얼 추출 (기기 인증용)
3. hash_password / verify_password: bcrypt 기반 비밀번호 해싱

.secret.key 파일은 nhis-macro-config에 보관됨.
"""

import subprocess
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from pathlib import Path


# --- [1. 보안 및 암호화 관리 클래스] ---
class SecurityManager:
    """암호화와 복호화를 담당하며, 키 파일을 영구 보존 관리합니다."""

    def __init__(self, key_path: str | Path) -> None:
        self.key_path = Path(key_path)
        self.key: bytes = self._ensure_key_exists()
        self.fernet = Fernet(self.key)

    def _ensure_key_exists(self) -> bytes:
        """키 파일이 있으면 읽고, 없으면 새로 생성하여 영구 저장합니다."""
        if self.key_path.exists():
            return self.key_path.read_bytes()

        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        new_key = Fernet.generate_key()
        self.key_path.write_bytes(new_key)
        print(f"🆕 새로운 보안 키가 생성되어 저장되었습니다: {self.key_path}")
        return new_key

    def encrypt_data(self, data: str) -> Optional[str]:
        if not data:
            return None
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, cipher_text: str) -> Optional[str]:
        if not cipher_text:
            return None
        try:
            return self.fernet.decrypt(cipher_text.encode()).decode()
        except Exception as e:
            return f"ERROR: Decryption Failed ({e})"


# --- [2. 하드웨어 식별 함수] ---
def get_hwid() -> str:
    """윈도우 메인보드 시리얼 번호 추출 (HWID)"""
    try:
        cmd = 'wmic baseboard get serialnumber'
        output = subprocess.check_output(cmd, shell=True).decode().split('\n')
        serial = output[1].strip()
        return serial
    except Exception:
        return "UNKNOWN_DEVICE"


# --- [3. 비밀번호 해싱 로직] ---
def hash_password(password: str) -> str:
    """관리자 비밀번호를 안전하게 해싱"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """입력된 비번과 DB의 해시값 대조"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


# --- [4. 비밀번호 복잡도 검증] ---
def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_alpha: bool = True,
    require_digit: bool = True,
) -> tuple[bool, str]:
    """비밀번호 복잡도 검증: 영문+숫자 조합, 기본 8자 이상

    Returns:
        (통과여부, 실패사유) — 통과 시 사유는 빈 문자열
    """
    if len(password) < min_length:
        return False, f"비밀번호는 {min_length}자 이상이어야 합니다."

    if require_alpha and not any(c.isalpha() for c in password):
        return False, "비밀번호에 영문자가 포함되어야 합니다."

    if require_digit and not any(c.isdigit() for c in password):
        return False, "비밀번호에 숫자가 포함되어야 합니다."

    return True, ""