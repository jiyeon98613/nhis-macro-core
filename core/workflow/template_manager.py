# core/template_manager.py
import json
from pathlib import Path

class TemplateManager:
    def __init__(self, storage_path: Path = None):
        if storage_path is None:
            # nhis-macro-config/templates 폴더를 기본으로 사용
            from env_setup import get_project_root
            self.storage_path = get_project_root() / "nhis-macro-config" / "templates"
        else:
            self.storage_path = storage_path
            
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.templates = {}
        self.load_templates()

    def load_templates(self):
        """저장된 모든 JSON 템플릿 로드"""
        for file in self.storage_path.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                self.templates[file.stem] = json.load(f)

    def get_template(self, doc_type: str):
        """특정 문서 타입의 템플릿 반환"""
        return self.templates.get(doc_type)

    def save_template(self, doc_type: str, data: dict):
        """새로운 양식 좌표 저장"""
        file_path = self.storage_path / f"{doc_type}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self.templates[doc_type] = data