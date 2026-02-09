# nhis-macro-core/core/security.py
import subprocess
import bcrypt
import os
from cryptography.fernet import Fernet

# --- [1. 보안 및 암호화 관리 클래스] ---
class SecurityManager:
    """
    암호화와 복호화를 담당하는 클래스.
    특정 경로를 스스로 찾지 않고 엔진에서 주입.
    """
    def __init__(self, key_path=None):
        self.cipher_suite = None
        if key_path:
            self.load_key(key_path)

    def load_key(self, key_path):
        """엔진에서 전달받은 경로의 키 파일을 읽어 로드합니다."""
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"🔑 키 파일을 찾을 수 없습니다: {key_path}")
        with open(key_path, "rb") as key_file:
            key = key_file.read()
        self.cipher_suite = Fernet(key)

    def encrypt_data(self, data: str) -> str:
        if not self.cipher_suite:
            raise ValueError("❌ 암호화 도구가 준비되지 않았습니다. load_key()를 먼저 실행하세요.")
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt_data(self, cipher_text: str) -> str:
        if not self.cipher_suite:
            raise ValueError("❌ 암호화 도구가 준비되지 않았습니다. load_key()를 먼저 실행하세요.")
        return self.cipher_suite.decrypt(cipher_text.encode()).decode()

# --- [2. 하드웨어 식별 함수 (전역)] ---
def get_hwid():
    """윈도우 메인보드 시리얼 번호 추출 (HWID)"""
    try:
        # wmic 명령어를 통해 메인보드 시리얼 번호를 가져옵니다.
        cmd = 'wmic baseboard get serialnumber'
        output = subprocess.check_output(cmd, shell=True).decode().split('\n')
        serial = output[1].strip()
        return serial
    except Exception:
        return "UNKNOWN_DEVICE"

# --- [3. 비밀번호 해싱 로직 (전역)] ---
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False    