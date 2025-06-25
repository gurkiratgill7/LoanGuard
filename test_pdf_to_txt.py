"""
Test script for pdf_to_txt.py module.
Tests both extract_text_from_pdf and text_to_paragraphs functions
using the PDF files in the tests directory.
"""

import os
import sys
from pathlib import Path

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from pdf_to_txt import extract_text_from_pdf, text_to_sections


def test_pdf_file(pdf_path: str):
    """Test both functions on a single PDF file."""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    try:
        # Read the PDF file as bytes
        with open(pdf_path, 'rb') as file:
            pdf_bytes = file.read()
        
        # Test extract_text_from_pdf
        print("\n1. Testing extract_text_from_pdf()...")
        extracted_text = extract_text_from_pdf(pdf_bytes)
        
        if extracted_text is None:
            print("   ❌ Failed to extract text from PDF")
            return
        
        print(f"   ✅ Successfully extracted text ({len(extracted_text)} characters)")
        print(f"   📄 Full extracted text:\n{extracted_text}\n")
        
        # Test text_to_paragraphs
        print("\n2. Testing text_to_paragraphs()...")
        paragraphs = text_to_sections(extracted_text)
        
        print(f"   ✅ Successfully split into {len(paragraphs)} paragraphs\n")
        
        for i, paragraph in enumerate(paragraphs, 1):
            print(f"   📝 Paragraph {i}: {paragraph}\n")
            
    except FileNotFoundError:
        print(f"   ❌ File not found: {pdf_path}")
    except Exception as e:
        print(f"   ❌ Error testing file: {e}")


def main():
    """Main function to run tests on all PDF files or a specific file."""
    tests_dir = Path(__file__).parent / "tests"
    
    if len(sys.argv) > 1:
        # Test specific file
        filename = sys.argv[1]
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        pdf_path = tests_dir / filename
        if pdf_path.exists():
            test_pdf_file(str(pdf_path))
        else:
            print(f"❌ File not found: {pdf_path}")
            print(f"Available PDF files in tests directory:")
            for pdf_file in sorted(tests_dir.glob("*.pdf")):
                print(f"  - {pdf_file.name}")
    else:
        # Test all PDF files in tests directory
        pdf_files = list(tests_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No PDF files found in {tests_dir}")
            return
        
        print(f"Found {len(pdf_files)} PDF files in tests directory")
        print("Testing all files...")
        
        for pdf_path in sorted(pdf_files):
            test_pdf_file(str(pdf_path))
        
        print(f"\n{'='*60}")
        print("✅ Testing completed!")
        print(f"{'='*60}")


if __name__ == "__main__":
    print("PDF to Text Testing Script")
    print("Usage:")
    print("  python test_pdf_to_txt.py                    # Test all PDF files")
    print("  python test_pdf_to_txt.py <filename>         # Test specific file")
    print("  python test_pdf_to_txt.py car_loan_agreement_predatory  # Example")
    
    main()
