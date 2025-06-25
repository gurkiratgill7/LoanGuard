import sys
import os
from pathlib import Path

# Add core to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from pdf_to_txt import extract_text_from_pdf, text_to_sections
from rule_analysis import run_rules_engine, _check_apr, _identify_loan_type

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_rule_analysis.py <pdf_file_path>")
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

    # Explicitly test _check_apr on the whole text
    loan_type = _identify_loan_type(text)
    apr_score, apr_flags = _check_apr(text, loan_type)
    print(f"\n_check_apr on full text:")
    print(f"Score: {apr_score}")
    print(f"Flags: {apr_flags}\n")

    # Run the rules engine as before
    sections = text_to_sections(text)
    total_risk_score, unique_flags = run_rules_engine(sections, text)

    print(f"\nTotal Risk Score: {total_risk_score}")
    print("\nUnique Flags:")
    for flag in unique_flags:
        print(flag)

if __name__ == "__main__":
    main()
