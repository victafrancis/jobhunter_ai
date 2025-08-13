# services/google_docs_utils.py
from __future__ import annotations
import io
from typing import Optional

from googleapiclient.http import MediaIoBaseUpload
from services.google_auth import get_drive_service

def create_google_doc_from_html(html: str, title: str, folder_id: Optional[str] = None) -> str:
    """
    Converts HTML to a Google Doc by uploading via Drive with conversion.
    Returns the webViewLink URL of the created Doc.
    """
    drive = get_drive_service()  # uses robust, shared auth (auto refresh + reauth)

    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
    }
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(
        io.BytesIO(html.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )

    created = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return created["webViewLink"]
