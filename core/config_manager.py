"""Configuration manager for saving/loading settings"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

class ConfigManager:
    DEFAULT_CONFIG = {
        "last_k_file": "",
        "last_material_source": "",
        "last_output_dir": "",
        "koomesh_path": "",
        "theme": "dark",
        "recent_files": []
    }

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_file = self.config_dir / "settings.json"
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load config from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()

    def save(self):
        """Save config to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value
        self.save()

    def add_recent_file(self, filepath: str):
        """Add file to recent files list"""
        recent = self.config.get("recent_files", [])
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        self.config["recent_files"] = recent[:10]  # Keep last 10
        self.save()
