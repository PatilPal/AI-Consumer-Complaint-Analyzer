"""
main.py — QuickKart Complaint Analyzer — FastAPI Backend
Run: uvicorn main:app --reload  (from the backend/ directory)
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Path fix so imports work from backend/ ────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from api_keys import init_db

# ─── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Consumer Complaint Analyzer",
    description="Escalation prediction, clustering, and root cause analysis for e-commerce complaints.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup: init DB + load model ─────────────────────────────────────────────

MODEL_PATH  = os.path.join(ROOT, "models", "escalation_model.pkl")
ENCODER_PATH = os.path.join(ROOT, "models", "label_encoder.pkl")

escalation_model = None
label_encoder    = None


@app.on_event("startup")
def startup():
    init_db()                            # creates api_keys table if absent
    global escalation_model, label_encoder
    try:
        escalation_model = joblib.load(MODEL_PATH)
        label_encoder    = joblib.load(ENCODER_PATH)
        print("[startup] Models loaded successfully.")
    except Exception as e:
        print(f"[startup] Warning — could not load models: {e}")
        print("[startup] /analyze will return heuristic scores only.")


# ─── Root Healthcheck ──────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "AI Consumer Complaint Analyzer"}


# ─── Schemas ───────────────────────────────────────────────────────────────────

COMPLAINT_TYPES = [
    "wrong_size",
    "color_mismatch",
    "fake_fabric",
    "return_not_picked",
    "refund_not_credited",
]

ROOT_CAUSE_MAP = {
    "wrong_size":          "Warehouse packing error suspected",
    "color_mismatch":      "Seller product listing fraud suspected",
    "fake_fabric":         "Supplier quality issue suspected",
    "return_not_picked":   "Logistics partner SLA breach suspected",
    "refund_not_credited": "Payment gateway / finance team delay suspected",
}

RISK_THRESHOLDS = {
    "Critical": 75,
    "High":     50,
    "Medium":   30,
}


class ComplaintRequest(BaseModel):
    complaint_text: str
    anger_score:    float = 0.5     # 0.0 – 1.0
    days_pending:   int   = 1
    repeat_count:   int   = 1


class AnalysisResponse(BaseModel):
    complaint_type: str
    risk_score:     int             # 0 – 100
    risk_level:     str             # Critical / High / Medium / Low
    escalation_prob: float          # 0.0 – 1.0
    root_cause:     str
    recommendation: str


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _detect_complaint_type(text: str) -> str:
    text = text.lower()
    if any(w in text for w in ["size", "xl", "xxl", "small", "large", "fit"]):
        return "wrong_size"
    if any(w in text for w in ["color", "colour", "pink", "red", "blue", "design", "photo"]):
        return "color_mismatch"
    if any(w in text for w in ["fake", "fabric", "rough", "quality", "duplicate"]):
        return "fake_fabric"
    if any(w in text for w in ["return", "pickup", "courier", "not picked"]):
        return "return_not_picked"
    if any(w in text for w in ["refund", "money", "credit", "payment", "amount"]):
        return "refund_not_credited"
    if any(w in text for w in ["not received", "not delivered", "missing", "parcel", "order", "package", "arrived"]):
        return "return_not_picked"
    return "wrong_size"   # default fallback


def _compute_risk_score(anger: float, days: int, repeat: int) -> int:
    score = int(anger * 50 + days * 2 + repeat * 5)
    return min(score, 100)


def _risk_level(score: int) -> str:
    if score >= RISK_THRESHOLDS["Critical"]:
        return "Critical"
    if score >= RISK_THRESHOLDS["High"]:
        return "High"
    if score >= RISK_THRESHOLDS["Medium"]:
        return "Medium"
    return "Low"


def _recommendation(risk_level: str, complaint_type: str) -> str:
    if risk_level == "Critical":
        return "Escalate immediately to senior support. Offer priority refund or replacement."
    if risk_level == "High":
        return "Assign to dedicated agent within 2 hours. Proactive customer callback recommended."
    if complaint_type == "return_not_picked":
        return "Coordinate with logistics partner and provide pickup tracking link."
    if complaint_type == "refund_not_credited":
        return "Initiate manual refund check with finance team within 24 hours."
    return "Standard resolution process. Expected SLA: 48 hours."


# ─── Main Endpoint ─────────────────────────────────────────────────────────────

@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Analyze a complaint — returns risk score, type, and root cause"
)
def analyze_complaint(req: ComplaintRequest):
    complaint_type = _detect_complaint_type(req.complaint_text)
    risk_score     = _compute_risk_score(req.anger_score, req.days_pending, req.repeat_count)
    risk_lvl       = _risk_level(risk_score)
    root_cause     = ROOT_CAUSE_MAP.get(complaint_type, "Unknown pattern")
    recommendation = _recommendation(risk_lvl, complaint_type)

    # Use XGBoost model if loaded, else fall back to heuristic
    escalation_prob = round(risk_score / 100, 2)
    if escalation_model is not None:
        try:
            features = np.array([[req.anger_score, req.days_pending, req.repeat_count]])
            prob = escalation_model.predict_proba(features)[0][1]
            escalation_prob = round(float(prob), 4)
            # Recalculate risk score blending model + heuristic
            heuristic = _compute_risk_score(req.anger_score, req.days_pending, req.repeat_count)
            risk_score = min(int((heuristic + prob * 100) / 2), 100)
            risk_lvl   = _risk_level(risk_score)
        except Exception as e:
            print(f"[analyze] Model prediction failed, using heuristic: {e}")

    # Save to SQLite
    import sqlite3
    import uuid
    from datetime import datetime

    db_path = os.path.join(ROOT, "db", "complaints.db")
    os.makedirs(os.path.join(ROOT, "db"), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            complaint_text TEXT,
            complaint_type TEXT,
            anger_score REAL,
            days_pending INTEGER,
            repeat_count INTEGER,
            risk_score INTEGER,
            risk_level TEXT,
            root_cause TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO complaints VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        str(uuid.uuid4()),
        req.complaint_text,
        complaint_type,
        req.anger_score,
        req.days_pending,
        req.repeat_count,
        risk_score,
        risk_lvl,
        root_cause,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    return AnalysisResponse(
        complaint_type  = complaint_type,
        risk_score      = risk_score,
        risk_level      = risk_lvl,
        escalation_prob = escalation_prob,
        root_cause      = root_cause,
        recommendation  = recommendation,
    )


# ─── Batch Endpoint (no auth — for dashboard internal use) ─────────────────────

@app.get("/complaints/summary", tags=["Analysis"])
def complaints_summary():
    """Returns aggregated stats from cluster_output.csv for the dashboard."""
    csv_path = os.path.join(ROOT, "data", "processed", "cluster_output.csv")
    try:
        df = pd.read_csv(csv_path)
        summary = {
            "total":          int(len(df)),
            "critical_count": int((df["Risk Level"] == "Critical").sum()),
            "high_count":     int((df["Risk Level"] == "High").sum()),
            "medium_count":   int((df["Risk Level"] == "Medium").sum()),
            "low_count":      int((df["Risk Level"] == "Low").sum()),
            "by_type":        df["complaint_type"].value_counts().to_dict(),
            "by_root_cause":  df["Root Cause"].value_counts().to_dict(),
            "avg_risk_score": round(float(df["Risk Score"].mean()), 1),
        }
        return summary
    except Exception as e:
        return {"error": str(e)}

@app.get("/complaints", tags=["Analysis"])
def get_complaints():
    import sqlite3
    db_path = os.path.join(ROOT, "db", "complaints.db")
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM complaints ORDER BY timestamp DESC", conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}