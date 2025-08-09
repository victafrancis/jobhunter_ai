# services/job_extraction_agent/preclean.py
from bs4 import BeautifulSoup

def heuristic_preclean(html_or_text: str) -> str:
    """
    Deterministic pre-clean. Remove obvious chrome from HTML, collapse whitespace,
    return plain text. Keeps it cheap and often avoids LLM cleaning entirely.
    """
    text = html_or_text or ""
    lower = text.lower()
    if "<html" in lower or "<div" in lower or "<p" in lower:
        soup = BeautifulSoup(text, "html.parser")
        for sel in ["nav", "footer", "header", "script", "style", "noscript", "form", "aside"]:
            for tag in soup.select(sel):
                tag.decompose()
        text = soup.get_text("\n", strip=True)

    # collapse blank lines
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    text = "\n".join(lines)

    # hard cap to avoid absurd token usage
    return text[:20000]
