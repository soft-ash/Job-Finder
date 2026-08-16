import os
import json
import gspread
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from core.config import logger, CREDENTIALS_PATH, SHEETS_SCOPES, BASE_DIR

# Use JSON (not pickle) — standard format that preserves account info reliably
TOKEN_FILE = os.path.join(BASE_DIR, "token_sheets.json")


class SheetsService:
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        if not self.sheet_id:
            logger.warning("No GOOGLE_SHEET_ID set — Sheets export disabled.")
            self.gc = None
        else:
            self.gc = self._authenticate()

    def _authenticate(self):
        creds = None

        # Load saved JSON token
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SHEETS_SCOPES)
                logger.info(f"Loaded Sheets token from {TOKEN_FILE}")
            except Exception as e:
                logger.warning(f"Could not load token: {e}")
                creds = None

        # Auto-refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing Google Sheets token...")
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                logger.info("Token refreshed and saved.")
            except Exception as e:
                logger.warning(f"Refresh failed ({e}) — will re-authenticate.")
                creds = None

        # Full OAuth flow if no valid token
        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error(f"credentials.json not found at {CREDENTIALS_PATH}")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SHEETS_SCOPES)
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")

            print("\n1. Open this URL to authorise Google Sheets (sign in as morat9511@gmail.com):")
            print(auth_url)
            code = input("2. Paste the authorisation code here: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Save as JSON for reliable reuse
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            logger.info(f"Token saved to {TOKEN_FILE}")

        logger.info("Google Sheets client ready.")
        return gspread.Client(auth=creds)

    def export(self, df: pd.DataFrame):
        if not self.gc or df.empty:
            logger.info("Nothing to export or Sheets not authenticated.")
            return

        try:
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            sheet = spreadsheet.sheet1

            # Write header if sheet is empty
            existing = sheet.get_all_values()
            if not existing:
                sheet.append_row(list(df.columns))

            # Clean and upload rows
            rows = df.fillna("").values.tolist()
            rows = [[str(v) for v in row] for row in rows]
            sheet.append_rows(rows)

            logger.info(f"✅ Exported {len(rows)} rows to '{spreadsheet.title}'")

        except Exception as e:
            err = str(e)
            import traceback
            tb = traceback.format_exc()
            
            if "has not been used in project" in tb or "is disabled" in tb:
                logger.error(
                    "❌ GOOGLE SHEETS API IS DISABLED ❌\n"
                    "Your Google Cloud project doesn't have the Google Sheets API enabled.\n"
                    "→ Fix it by clicking this link and clicking 'Enable':\n"
                    "→ https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=754624407956"
                )
            elif "403" in err or "PERMISSION" in err.upper() or isinstance(e, PermissionError):
                logger.error(
                    "❌ GOOGLE SHEETS ACCESS DENIED (403) ❌\n"
                    f"The account you signed in with does NOT have access to the spreadsheet.\n"
                    f"→ The sheet ID is: {self.sheet_id}\n"
                    f"→ Make sure you sign in as morat9511@gmail.com when prompted.\n"
                    f"→ To try again, delete {TOKEN_FILE} and restart the script."
                )
            else:
                logger.error(f"Sheets export failed: {repr(e)}\n{tb}")
