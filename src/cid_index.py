import json
import time
from pathlib import Path

INDEX_PATH = Path("cid_index.json")

def _load():
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text("{}", encoding="utf-8")
    return json.loads(INDEX_PATH.read_text(encoding="utf-8") or "{}")

def _save(obj):
    INDEX_PATH.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def set_template(user_id_hash_hex: str, template_cid: str, template_cid_hash_hex: str, key_version: int):
    db = _load()
    db[user_id_hash_hex] = {
        "template_cid": template_cid,
        "template_cid_hash": template_cid_hash_hex,
        "key_version": int(key_version),
        "updated_at": int(time.time())
    }
    _save(db)

def get_template_cid(user_id_hash_hex: str) -> str:
    db = _load()
    rec = db.get(user_id_hash_hex)
    if not rec:
        raise KeyError(f"Missing template CID for {user_id_hash_hex}")
    return rec["template_cid"]
