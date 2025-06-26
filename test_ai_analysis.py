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
    # ... and so on ...

# ... The rest of your script is unchanged ...

if __name__ == "__main__":
    main()