import os
from datetime import date
import pdfkit

# where PDFs go
SAVE_DIR = "saved_documents"
os.makedirs(SAVE_DIR, exist_ok=True)

def export_html_to_pdf(
      html_content: str, 
      filename: str, 
      margin: str="0.75in",
      fontsize: str="12pt"
    ) -> str:
    """
    Render the given HTML string to a PDF file named `filename` in SAVE_DIR.
    Returns the full path to the generated PDF.
    """
    file_path = os.path.join(SAVE_DIR, filename)

    # wrap in a little HTML + CSS so wkhtmltopdf uses Arial
    full_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <style>
          body {{
            font-family: Arial, sans-serif;
            font-size: {fontsize};
            margin: {margin};
            line-height: 1.4;
          }}
          h1,h2,h3,h4 {{ margin-top: 1em; margin-bottom: .5em; }}
          ul {{ margin-left: 1em; }}
          p {{
            margin: 0;
            padding: 0 0 0 0;
          }}
        </style>
      </head>
      <body>
        {html_content}
      </body>
    </html>
    """
    pdfkit.from_string(full_html, file_path)
    print(f"✅ PDF saved to {file_path}")
    return file_path

def export_cover_letter_pdf(html_content: str, job_title: str, company: str) -> str:
    """
    Build a filename like "2025-08-06_Acme_Corp_cover_letter.pdf"
    then call export_html_to_pdf.
    """
    today = date.today().isoformat()
    safe = company.replace(" ", "_")
    filename = f"{today}_{safe}_cover_letter.pdf"
    return export_html_to_pdf(html_content, filename, fontsize="14pt")

def export_resume_pdf(html_content: str, job_title: str, company: str) -> str:
    """
    Build a filename like "2025-08-06_Acme_Corp_resume.pdf"
    then call export_html_to_pdf.
    """
    today = date.today().isoformat()
    safe = company.replace(" ", "_")
    filename = f"{today}_{safe}_resume.pdf"
    return export_html_to_pdf(html_content, filename, margin="0.25in")
