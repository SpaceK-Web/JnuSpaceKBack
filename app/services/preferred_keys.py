import json
from pathlib import Path
from threading import Lock

DATA_PATH = Path(__file__).parent.parent / "data" / "preferred_keys.json"
_lock = Lock()


def load_keys() -> list[dict]:
    """선호 키 전체 목록 로드"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_key_names() -> list[str]:
    """선호 키 이름만 리스트로 반환"""
    return [item["key"] for item in load_keys()]


def get_keys_with_descriptions() -> str:
    """프롬프트에 삽입할 키 설명 텍스트 생성"""
    keys = load_keys()
    lines = []
    for k in keys:
        line = f'- "{k["key"]}": {k["description"]}'
        if k.get("examples"):
            line += f'  (예: {", ".join(k["examples"])})'
        if k.get("not_examples"):
            line += f'  (제외: {", ".join(k["not_examples"])})'
        lines.append(line)
    return "\n".join(lines)


def promote_custom_key(key: str, description: str):
    """자유 생성된 키를 선호 키로 승격"""
    with _lock:
        keys = load_keys()
        existing = {k["key"] for k in keys}

        if key not in existing:
            keys.append({
                "key": key,
                "description": description,
                "examples": [],
                "not_examples": []
            })
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(keys, f, ensure_ascii=False, indent=4)
            print(f"🆕 선호 키 승격: {key}")
