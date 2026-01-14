import pdfplumber
import docx2txt
import re

def extract_text(file):
    if file.name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    elif file.name.endswith(".docx"):
        return docx2txt.process(file)

    else:
        raise ValueError("Unsupported format")

def extract_candidate_name(text):
    return text.split("\n")[0][:50]
