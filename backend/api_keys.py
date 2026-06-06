"""
api_keys.py — API Key Management Router
Self-contained FastAPI router for generating, listing, and revoking API keys.
Keys are stored in SQLite. Plug into main.py with one import.
"""

import sqlite3
import secrets
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ─── Database Setup ────────────────────────────────────────────────────────────

DB_PATH = "db/api_keys.db"


def get_db():
    import os
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash    TEXT    NOT NULL UNIQUE,
            key_prefix  TEXT    NOT NULL,
            label       TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            revoked     INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    """
    Middleware-style dependency — checks X-API-Key header on protected routes.
    Raises 401 if missing or invalid.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required.")
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE key_hash = ? AND revoked = 0",
        (_hash_key(x_api_key),)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key.")
    return x_api_key


# ─── Schemas ───────────────────────────────────────────────────────────────────

class KeyCreateRequest(BaseModel):
    label: str = ""


class KeyRevokeRequest(BaseModel):
    key_prefix: str   # first 8 chars of the key — enough to identify without exposing full key


# ─── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/keys", tags=["API Keys"])


@router.post("/generate", summary="Generate a new API key")
def generate_key(body: KeyCreateRequest):
    raw_key = "qk-" + secrets.token_hex(32)   # e.g. qk-a3f9...
    key_hash = _hash_key(raw_key)
    key_prefix = raw_key[:11]                  # "qk-" + 8 hex chars
    created_at = datetime.utcnow().isoformat()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO api_keys (key_hash, key_prefix, label, created_at) VALUES (?, ?, ?, ?)",
            (key_hash, key_prefix, body.label, created_at)
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "api_key": raw_key,          # returned ONCE — store it securely
        "key_prefix": key_prefix,
        "label": body.label,
        "created_at": created_at,
        "note": "This key will not be shown again. Copy it now."
    }


@router.get("/list", summary="List all active API keys (prefixes only)")
def list_keys():
    conn = get_db()
    rows = conn.execute(
        "SELECT key_prefix, label, created_at, revoked FROM api_keys ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/revoke", summary="Revoke an API key by prefix")
def revoke_key(body: KeyRevokeRequest):
    conn = get_db()
    result = conn.execute(
        "UPDATE api_keys SET revoked = 1 WHERE key_prefix = ? AND revoked = 0",
        (body.key_prefix,)
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Key not found or already revoked.")
    return {"message": f"Key '{body.key_prefix}...' has been revoked."}
