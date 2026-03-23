# core/security.py
import subprocess
import bcrypt
import os
from cryptography.fernet import Fernet
from pathlib import Path

# --- [1. 보안 및 암호화 관리 클래스] ---
class SecurityManager:
    """
    암호화와 복호화를 담당하며, 키 파일을 영구 보존 관리합니다.
    """
    def __init__(self, key_path):
        self.key_path = Path(key_path)
        self.key = self._ensure_key_exists()
        self.fernet = Fernet(self.key)

    def _ensure_key_exists(self):
        """키 파일이 있으면 읽고, 없으면 새로 생성하여 영구 저장합니다."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            # 상위 폴더가 없으면 생성
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            new_key = Fernet.generate_key()
            self.key_path.write_bytes(new_key)
            print(f"🆕 새로운 보안 키가 생성되어 저장되었습니다: {self.key_path}")
            return new_key

    def encrypt_data(self, data: str) -> str:
        if not data: return None
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, cipher_text: str) -> str:
        if not cipher_text: return None
        # 데이터가 이미 바이트 형태가 아닐 경우를 대비해 처리
        try:
            return self.fernet.decrypt(cipher_text.encode()).decode()
        except Exception as e:
            # 암호화되지 않은 평문이 들어올 경우의 예외 처리
            return f"ERROR: Decryption Failed ({e})"

# --- [2. 하드웨어 식별 함수] ---
def get_hwid():
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