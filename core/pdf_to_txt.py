import fitz  #PyMuPDF
import re
from typing import Optional

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

    # Use regex to split the text by one or more blank lines.
    # This is more robust than text.split('\n\n').
    # The regex pattern looks for two newlines separated by any amount of whitespace.
    raw_paragraphs = re.split(r'\n\s*\n', text)
    
    # Clean up the results, removing any empty strings that result from the split.
    cleaned_paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
    
    return cleaned_paragraphs
