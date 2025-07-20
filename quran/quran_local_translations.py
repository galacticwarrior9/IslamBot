import json
import os
from pathlib import Path
from typing import Dict, Optional

class LocalTranslations:
    def __init__(self, translations_dir: str = "./quran/quran_local_translations"):
        self.translations_dir = Path(translations_dir)
        self.translations = self._load_all_translations()

    def _load_all_translations(self) -> Dict[str, dict]:
        """Load all translation JSON files from the directory"""
        translations = {}
        if not self.translations_dir.exists():
            return translations

        for file in self.translations_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    trans_id = data["metadata"]["id"]
                    # print(f"+ Local translation found: {trans_id}")
                    translations[trans_id] = data
            except Exception as e:
                print(f"Error loading {file}: {e}")
        return translations

    def get_verse(self, translation_id: str, surah: int, verse: int) -> Optional[str]:
        if translation_id not in self.translations:
            return None

        translation = self.translations[translation_id]
        surah_str = str(surah)
        verse_str = str(verse)

        try:
            surah_data = translation["verses"].get(surah_str)
            if not surah_data:
                return None

            verse_data = surah_data["verses"].get(verse_str)
            if not verse_data:
                return None

            return verse_data["text"]
        except KeyError:
            return None

    def get_translation_name(self, translation_id: str) -> Optional[str]:
        """Get the display name of a translation"""
        if translation_id in self.translations:
            return self.translations[translation_id]["metadata"].get("name")
        return None

    def get_all_ids(self) -> list:
        """Get all available local translation IDs"""
        return list(self.translations.keys())
