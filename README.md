# SmartHire AI — Full Pipeline

End-to-end job email filtering and CV matching system built in Python.

---

## Workflow

```
Gmail → Gmail API/OAuth → Email Collection → TF-IDF + Naive Bayes classifier
→ Relevant jobs → Gemini AI extraction (JSON) → CV PDF extraction
→ CV ↔ Job matching (Skill / Experience / Location / Semantic)
→ Score 0–100 → ⭐ 1–5 ranking → Google Sheets + CSV export
```

---

## Project Files

| File | Purpose |
|---|---|
| `smarthire_workflow.py` | Complete pipeline script |
| `credentials.json` | Google Cloud Desktop OAuth client (keep secret) |
| `cv.pdf` | Your CV — place here before running |
| `token.pickle` | Gmail OAuth token (auto-created) |
| `token_sheets.pickle` | Sheets OAuth token (auto-created) |
| `job_email_classifier.pkl` | Trained Naive Bayes model (auto-created) |
| `smarthire_results.csv` | Final ranked results (auto-created) |
| `.env.example` | Template for required secrets |

---

## Setup (One-Time)

### 1. Python Environment

```bash
cd /home/rafat/Documents/ai_project
python3 -m venv venv
source venv/bin/activate
pip install pandas scikit-learn matplotlib seaborn joblib \
            google-auth google-auth-oauthlib google-auth-httplib2 \
            google-api-python-client beautifulsoup4 \
            google-generativeai gspread oauth2client PyMuPDF
```

### 2. Google Cloud Project

1. Go to https://console.cloud.google.com
2. Create a new project (e.g. SmartHire AI)
3. Enable Gmail API and Google Sheets API
4. Go to APIs & Services → Credentials → Create Credentials → OAuth client ID
5. Application type: Desktop App
6. Download the JSON → rename to credentials.json
7. Place it in /home/rafat/Documents/ai_project/

### 3. Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Create an API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-key-here"
```

### 4. Google Sheet

1. Create a blank Google Sheet
2. Copy the Sheet ID from the URL:
   https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit
3. Set it:

```bash
export GOOGLE_SHEET_ID="your-sheet-id-here"
```

### 5. Upload Your CV

Place your CV PDF in the project directory:

```bash
cp /path/to/your/cv.pdf /home/rafat/Documents/ai_project/cv.pdf
```

---

## Run

```bash
cd /home/rafat/Documents/ai_project
source venv/bin/activate
export GEMINI_API_KEY="your-key-here"
export GOOGLE_SHEET_ID="your-sheet-id-here"
python3 smarthire_workflow.py
```

### What happens during the run

| Step | What you'll see |
|---|---|
| ML training | Accuracy / Precision / Recall / F1 printed |
| Gmail OAuth | A URL is printed - open it, sign in, paste the code back |
| Email fetching | Progress messages for each email |
| Gemini extraction | One line per email being processed |
| CV analysis | Your structured profile printed as JSON |
| Matching | Score breakdown per job |
| Results | Ranked table in terminal + CSV saved |
| Sheets OAuth | A second URL for Sheets permission (if GOOGLE_SHEET_ID set) |
| Export | Confirmation of rows written to your Sheet |

---

## Scoring Weights

| Component | Weight |
|---|---|
| Skill match (TF overlap) | 40% |
| Experience match | 25% |
| Semantic similarity (Gemini) | 25% |
| Location match | 10% |

## Star Rating

| Score | Stars |
|---|---|
| 85-100 | 5 stars |
| 70-84 | 4 stars |
| 50-69 | 3 stars |
| 30-49 | 2 stars |
| 0-29 | 1 star |

---

## Security Notes

Never commit credentials.json, token.pickle, token_sheets.pickle,
your CV, or your API key to a public repository.

Add this to .gitignore:

```
credentials.json
token.pickle
token_sheets.pickle
cv.pdf
.env
smarthire_results.csv
job_email_classifier.pkl
venv/
```
# Job-Finder
