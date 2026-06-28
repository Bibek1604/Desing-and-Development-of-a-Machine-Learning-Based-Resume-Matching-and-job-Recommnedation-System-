"""Resume text extraction from PDF / DOCX / TXT files."""
import os


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        if ext in (".docx", ".doc"):
            return _extract_docx(file_path)
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                return fh.read()
    except Exception:
        # Parsing should never crash an upload; fall back to empty text.
        return ""
    return ""


def _extract_pdf(file_path: str) -> str:
    from pdfminer.high_level import extract_text as pdf_extract
    return pdf_extract(file_path) or ""


def _extract_docx(file_path: str) -> str:
    import docx
    document = docx.Document(file_path)
    return "\n".join(p.text for p in document.paragraphs)
