# hushh_mcp/vault/json_vault.py

import os
import json
from typing import Any
from hushh_mcp.vault.encrypt import encrypt_data, decrypt_data
from hushh_mcp.types import EncryptedPayload

VAULT_KEY_ENV = "VAULT_ENCRYPTION_KEY"

class VaultError(Exception):
    pass

def get_vault_key() -> str:
    key = os.getenv(VAULT_KEY_ENV)
    if not key:
        raise VaultError(f"Vault encryption key not set in environment variable {VAULT_KEY_ENV}")
    return key

def load_encrypted_json(path: str) -> Any:
    key = get_vault_key()
    with open(path, "r", encoding="utf-8") as f:
        payload_dict = json.load(f)
    payload = EncryptedPayload(**payload_dict)
    plaintext = decrypt_data(payload, key)
    return json.loads(plaintext)

def save_encrypted_json(data: Any, path: str):
    key = get_vault_key()
    plaintext = json.dumps(data, ensure_ascii=False, indent=2)
    payload = encrypt_data(plaintext, key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload.dict(), f, ensure_ascii=False, indent=2)
