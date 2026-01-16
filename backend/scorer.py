import pdfplumber
import docx

def extract_text(file) -> str:
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return "\n".join(p.page.extract_text() or "" for p in pdf.pages)
    else:
        doc = docx.Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

def extract_candidate_name(text: str) -> str:
    lines = text.splitlines()
    return lines[0].strip() if lines else "Unknown"
