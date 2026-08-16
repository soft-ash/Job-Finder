import os
import pickle
import base64
from bs4 import BeautifulSoup
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from core.config import logger, CREDENTIALS_PATH, GMAIL_TOKEN_PATH, GMAIL_SCOPES

class GmailService:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(GMAIL_TOKEN_PATH):
            with open(GMAIL_TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error(f"Credentials not found at {CREDENTIALS_PATH}")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, GMAIL_SCOPES)
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")

            print("1. Open this URL in your browser:")
            print(auth_url)
            print("\n2. Sign in, approve access, and copy the code Google gives you.")
            code = input("3. Paste the authorization code here: ").strip()

            flow.fetch_token(code=code)
            creds = flow.credentials
            
            with open(GMAIL_TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)

        return build("gmail", "v1", credentials=creds)

    def search_emails(self, query: str, max_results: int = 20):
        if not self.service:
            logger.error("Gmail service not authenticated.")
            return []

        results = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        return results.get("messages", [])

    def get_email_body(self, payload: dict) -> str:
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    break
                elif mime_type == "text/html" and "data" in part.get("body", {}):
                    html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                    body = BeautifulSoup(html, "html.parser").get_text()
                elif "parts" in part:
                    body = self.get_email_body(part)
                    if body:
                        break
        elif "data" in payload.get("body", {}):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        return body

    def get_email_details(self, msg_id: str) -> dict:
        if not self.service:
            return {}

        msg = self.service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        headers = msg["payload"]["headers"]
        
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "(Unknown Date)")
        
        body = self.get_email_body(msg["payload"])
        
        return {
            "id": msg_id,
            "subject": subject,
            "from": sender,
            "date": date,
            "body": body.strip()
        }
