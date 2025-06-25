import fitz  #PyMuPDF
import re
from typing import Optional, List

def extract_text_from_pdf(pdf_bytes: bytes) -> Optional[str]:
    try:
        # Open the PDF from the byte stream in memory
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        full_text = ""
        # Iterate through each page and extract text
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text("text")
            
        return full_text
    
    #error parsing file
    except Exception as e:
        print(f"Error processing PDF file: {e}")
        return None

def text_to_paragraphs(text: Optional[str]) -> List[str]:
    if not text:
        return []

    # Split at lines that start with a Roman numeral (I, II, III, IV, etc.) followed by a period and a space
    # Roman numerals: I, II, III, IV, V, VI, VII, VIII, IX, X, ...
    # Regex: ^[IVXLCDM]+\.\s
    # Use re.MULTILINE to match at the start of lines
    raw_paragraphs = re.split(r'(?m)^([IVXLCDM]+\.)\s', text)

    # The split will keep the delimiters (the Roman numerals) as separate elements, so we need to recombine them
    paragraphs = []
    i = 1 if raw_paragraphs and raw_paragraphs[0].strip() == '' else 0
    while i < len(raw_paragraphs):
        if i + 1 < len(raw_paragraphs):
            para = f"{raw_paragraphs[i]}. {raw_paragraphs[i+1]}".strip()
            paragraphs.append(para)
            i += 2
        else:
            # If there's a trailing chunk without a numeral
            if raw_paragraphs[i].strip():
                paragraphs.append(raw_paragraphs[i].strip())
            i += 1

    return paragraphs
