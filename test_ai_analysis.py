# test_ai_analysis.py
import sys
import os
import toml # Import the new library
from pathlib import Path

# This function loads the secret into the environment
def load_secrets():
    """Loads secrets from .streamlit/secrets.toml into environment variables."""
    secrets_path = Path(__file__).parent / ".streamlit/secrets.toml"
    if secrets_path.exists():
        secrets = toml.load(secrets_path)
        for key, value in secrets.items():
            os.environ[key] = str(value)

# Load secrets at the very beginning
load_secrets()

# Add core to sys.path after loading secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Your existing imports
from pdf_to_txt import extract_text_from_pdf, text_to_sections
from ai_analysis import run_ai_analysis

def main():
    # The rest of your main function remains exactly the same...
    if len(sys.argv) != 2:
        print("Usage: python test_ai_analysis.py <pdf_file_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]


    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    text = extract_text_from_pdf(pdf_bytes)
    if not text:
        print("Failed to extract text from PDF.")
        sys.exit(1)

    sections = text_to_sections(text)
    print(f"Extracted {len(sections)} sections from PDF")
    
    # Run AI analysis
    ai_risk_score, ai_flags = run_ai_analysis(sections)
    
    print(f"\nAI Analysis Results:")
    print(f"AI Risk Score: {ai_risk_score}")
    print(f"\nAI Flags ({len(ai_flags)} found):")
    for i, flag in enumerate(ai_flags, 1):
        print(f"\n[Flag {i}]")
        print(f"Type: {flag['type']}")
        print(f"Title: {flag['title']}")
        print(f"Explanation: {flag['explanation']}")
        print(f"Context: {flag['context'][:100]}...")

if __name__ == "__main__":
    main()
