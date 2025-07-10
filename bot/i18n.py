import json
import os
from functools import lru_cache
from typing import Dict

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")
DEFAULT_LANG = "en"


@lru_cache(maxsize=None)
def load_lang(lang: str) -> Dict[str, str]:
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    if not os.path.exists(path):
        path = os.path.join(LOCALES_DIR, f"{DEFAULT_LANG}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str | None = None) -> str:
    data = load_lang(lang or DEFAULT_LANG)
    return data.get(key, key)