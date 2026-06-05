# AI Consumer Complaint Analyzer

A machine learning system that predicts complaint escalation risk, detects systemic patterns, and suggests root causes for Indian e-commerce clothing complaints.

## Project Overview

Most complaint systems only categorize complaints. We built a predictive intelligence layer that does three things automatically:

1. **Escalation Prediction** — Scores every complaint 0–100% for escalation risk using XGBoost
2. **Systemic Pattern Detection** — Groups similar complaints using DBSCAN and K-Means clustering to detect bulk issues
3. **Root Cause Suggestion** — Automatically suggests why a problem is happening based on complaint patterns

## Domain

Indian e-commerce — Flipkart, Meesho, Amazon IN
Starting scope: Clothing and fashion complaints only

## Team

| Member | Role |
|--------|------|
| Pal (Lead) | Escalation Prediction Model + GitHub + Demo |
| Bhoomin | Data Pipeline + NLP + FastAPI Backend |
| Kavitha | Clustering Model + Streamlit Dashboard |
| Chetna | Customer Facing Frontend App |
| Vivek | Data Collection and Labeling |

## Project Structure

```
AI-Consumer-Complaint-Analyzer/
├── backend/          # FastAPI backend 
├── dashboard/        # Streamlit manager dashboard 
├── data/
│   ├── raw/          # Original complaint dataset
│   └── processed/    # Cleaned data, embeddings, cluster output
├── frontend/         # QuickKart customer app HTML/CSS/JS 
├── models/           # Trained ML model pkl files
├── notebooks/        # Jupyter notebooks for all members
└── requirements.txt
```

## Tech Stack

- **ML Models** — XGBoost, DBSCAN, K-Means, Scikit-learn
- **NLP** — IndicBERT, HuggingFace, spaCy, NLTK
- **Backend** — Python, FastAPI, Pydantic, SQLite
- **Dashboard** — Streamlit, Plotly, Pandas
- **Frontend** — HTML, CSS, JavaScript
- **Dev Tools** — Jupyter Notebook, Anaconda, GitHub

## How to Run

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Start the backend API
```bash
cd backend
uvicorn main:app --reload
```

### Step 3 — Open the customer app
Open `frontend/index.html` in any browser

### Step 4 — Run the manager dashboard
```bash
streamlit run dashboard/dashboard.py
```

## Demo

Two screens on demo day:
- **Screen 1** — QuickKart customer app with complaint chatbox
- **Screen 2** — Internal manager dashboard showing escalation risk, clusters, and root cause in real time

## Complaint Types Covered

1. Wrong size or fit delivered
2. Color or design not matching online photo
3. Fake, low quality, or damaged fabric
4. Return not picked up by courier
5. Refund not credited after return accepted

## Data Source

Primary: consumerhelpline.gov.in (National Consumer Helpline)
Supplement: Twitter complaints, app store reviews, Kaggle datasets
Language: English and Hinglish (handled by IndicBERT)
