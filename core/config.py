import os
import logging

from dotenv import load_dotenv

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
GMAIL_TOKEN_PATH = os.path.join(BASE_DIR, "token.pickle")
SHEETS_TOKEN_PATH = os.path.join(BASE_DIR, "token_sheets.pickle")
CV_PDF_PATH = os.path.join(BASE_DIR, "cv.pdf")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "job_email_classifier.pkl")
CSV_EXPORT_PATH = os.path.join(BASE_DIR, "Job_result.csv")

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, ".env"))

# API Keys & IDs
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

# Scopes
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Weights for matching algorithm
WEIGHTS = {
    "skill": 0.40,
    "experience": 0.25,
    "location": 0.10,
    "semantic": 0.25,
}

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SmartHire")
