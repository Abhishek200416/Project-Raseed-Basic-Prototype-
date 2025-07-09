import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]
ISSUER_ID = "INSERT_YOUR_ISSUER_ID"  # ← set this
CLASS_ID  = f"{ISSUER_ID}.receipt_insight_class"

def create_wallet_pass(title: str, details: str) -> str:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT, scopes=SCOPES
    )
    service = build("walletobjects", "v1", credentials=creds)
    obj = {
        "id": f"{ISSUER_ID}.{os.urandom(6).hex()}",
        "classId": CLASS_ID,
        "genericType": "GENERIC_PASS",
        "title": title,
        "textModulesData": [{"header": "Details", "body": details}]
    }
    created = service.genericobject().insert(body=obj).execute()
    return created.get("id", "")
