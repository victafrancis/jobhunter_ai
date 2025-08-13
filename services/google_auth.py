# services/google_auth.py
# requirements: google-api-python-client, google-auth-httplib2, google-auth-oauthlib

from __future__ import annotations
import io
import os
import pickle
import pathlib
from typing import Iterable, Tuple

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Where to keep tokens outside your repo
APP_DIR = pathlib.Path.home() / ".jobhunter_ai" / "google"
APP_DIR.mkdir(parents=True, exist_ok=True)

CREDS_PATH = pathlib.Path("credentials.json")  # download from Google Cloud → OAuth client

DOCS_SCOPES   = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file"]
DRIVE_SCOPES  = ["https://www.googleapis.com/auth/drive.file"]  # used for HTML→Docs upload
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _token_path_for(scopes: Iterable[str]) -> pathlib.Path:
    # Different tokens per scope set to avoid scope mismatch issues
    tag = "-".join(sorted(s.split("/")[-1] for s in scopes))  # simple stable tag
    return APP_DIR / f"token-{tag}.pickle"

def _atomic_save_token(path: pathlib.Path, creds: Credentials) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(creds, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def _load_token(path: pathlib.Path) -> Credentials | None:
    if path.exists() and path.stat().st_size > 0:
        with open(path, "rb") as f:
            return pickle.load(f)
    return None

def _new_flow(scopes: Iterable[str]) -> Credentials:
    if not CREDS_PATH.exists():
        raise FileNotFoundError(
            "credentials.json not found. Download your OAuth client JSON from Google Cloud Console."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), scopes=list(scopes))
    # Local app: opens a browser and captures the code automatically
    creds = flow.run_local_server(port=0, prompt="consent", include_granted_scopes="true")
    return creds

def _get_service(api: str, version: str, scopes: Iterable[str]):
    token_path = _token_path_for(scopes)
    creds = _load_token(token_path)
    try:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = _new_flow(scopes)
            _atomic_save_token(token_path, creds)
    except Exception:
        # Covers invalid_grant and other refresh problems
        try:
            token_path.unlink(missing_ok=True)
        except Exception:
            pass
        creds = _new_flow(scopes)
        _atomic_save_token(token_path, creds)

    return build(api, version, credentials=creds, cache_discovery=False)

def get_docs_service():
    # Docs API often needs Drive scope when creating files programmatically
    return _get_service("docs", "v1", DOCS_SCOPES)

def get_drive_service():
    return _get_service("drive", "v3", DRIVE_SCOPES)

def get_sheets_service():
    return _get_service("sheets", "v4", SHEETS_SCOPES)
