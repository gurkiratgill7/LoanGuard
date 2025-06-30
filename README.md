# LoanGuard🛡️ LoanGuard: AI-Powered Loan Agreement Analyzer
![alt text](https://img.shields.io/badge/Python-3.9%2B-blue.svg)

![alt text](https://img.shields.io/badge/Streamlit-1.25%2B-red.svg)

![alt text](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Transformers-yellow.svg)

![alt text](https://img.shields.io/badge/License-MIT-green.svg)
LoanGuard is an AI-powered tool designed to demystify complex financial documents and protect consumers from predatory lending practices. By uploading a loan agreement, users can receive an instant, easy-to-understand analysis that highlights potential risks, hidden fees, and consumer-unfriendly clauses.
✨ Live Demo
You can access the live, deployed application here:
[https://YOUR-STREAMLIT-APP-URL-HERE]
🎯 Project Overview
Problem: Predatory lending traps millions of people in cycles of debt. The agreements are often dense with confusing legal jargon, making it nearly impossible for the average person to identify unfair terms like hidden fees, excessive interest rates, or prepayment penalties before it's too late.
Solution: LoanGuard acts as a personal AI financial advocate. It employs a sophisticated dual-engine analysis to scan loan agreements and provide a clear, actionable risk report.
Rule-Based Engine: A fast, deterministic engine that uses a comprehensive set of curated rules and regular expressions to catch unambiguous red flags. It performs context-aware checks, such as comparing a loan's APR against industry benchmarks for that specific loan type (e.g., Mortgage, Car Loan, Payday Loan).
AI Analysis Engine: A powerful local Natural Language Processing (NLP) model (facebook/bart-large-mnli) that goes beyond keywords. It analyzes the semantic meaning of clauses to identify multiple nuanced risks within a single section, such as deceptive language, hidden fees, and clauses that encourage debt cycles.
By combining these two approaches, LoanGuard provides a robust and reliable analysis, empowering users to make safer financial decisions.
🚀 Key Features
Dual-Engine Analysis: Combines a fast, precise rule-based system with a deep, context-aware AI model.
PDF Document Processing: Users can directly upload PDF files for analysis.
Dynamic APR Scoring: The risk associated with an APR is dynamically calculated based on the detected loan type (e.g., a 15% APR is normal for a credit card but high for a mortgage).
Multi-Risk Detection: The AI can identify several distinct predatory clauses within a single section of the document.
Smart De-duplication: Intelligently merges findings from both engines to provide a clean, non-redundant final report.
Interactive Report: Presents findings in an easy-to-understand format with expandable sections for critical risks, warnings, and even positive (pro-consumer) findings.
🛠️ Technology Stack
Backend: Python
Frontend / UI: Streamlit
AI / NLP: Hugging Face Transformers (pipeline), PyTorch
PDF Processing: PyMuPDF
Code Hosting & CI/CD: GitHub & Codespaces
Deployment: Streamlit Community Cloud
⚙️ Local Setup and Running Instructions
Follow these steps to run LoanGuard on your local machine.
Prerequisites
Git
Python 3.9+
Step-by-Step Guide
1. Clone the Repository
Generated bash
git clone https://github.com/your-username/LoanGuard.git
cd LoanGuard
Use code with caution.
Bash
2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.
On macOS / Linux:
Generated bash
python3 -m venv venv
source venv/bin/activate
Use code with caution.
Bash
On Windows:
Generated bash
python -m venv venv
.\venv\Scripts\activate
Use code with caution.
Bash
3. Install Dependencies
This will install all necessary libraries, including Streamlit and the large AI model dependencies (torch, transformers). This step may take several minutes.
Generated bash
pip install -r requirements.txt
Use code with caution.
Bash
4. Set up the Secret Token (for API version, optional for local)
LoanGuard is configured to run a local model and does not require an API key to run. However, if you switch to the API version, you will need a Hugging Face token.
Create a file at .streamlit/secrets.toml.
Add your token to this file in the following format:
Generated toml
HF_TOKEN = "hf_YourHuggingFaceTokenHere"
Use code with caution.
Toml
5. Run the Streamlit App
Generated bash
streamlit run app.py
Use code with caution.
Bash
The application should automatically open in a new browser tab. The first time you run it, there will be a one-time delay as the AI model is downloaded and loaded into memory.
📖 How to Use the App
Open the Application: Navigate to the local URL provided by Streamlit (usually http://localhost:8501) or the live demo site.
Upload a PDF: Click the "Choose a PDF file" button and select a loan agreement document from your computer.
Analyze: Click the "Analyze Document" button to start the analysis.
Review the Report: Within moments, an interactive report will appear. It will show an overall risk score and expandable sections detailing any Critical Risks, Warnings, and Positive Findings detected in your document.
⚖️ Ethical Considerations
Not a Substitute for Professional Advice: The application's primary ethical consideration is ensuring users understand that it is an educational tool, not a replacement for qualified legal or financial advice. This is stated clearly in the disclaimer.
Accuracy and Limitations: We acknowledge that no AI is perfect. The tool may produce false positives or miss certain risks. The goal is to empower users with a powerful "second opinion," not to provide a definitive judgment.
Data Privacy: By running the model locally, this version of the application enhances user privacy, as the sensitive document content is never sent to an external third-party API. All processing happens within the user's session.
🧠 Challenges & Lessons Learned
API Rate Limiting: We initially used the Hugging Face Inference API but quickly hit rate limits during testing. This prompted a pivot to running the model locally, which presented its own challenges with dependency management but ultimately resulted in a more robust and private application.
AI Analysis Granularity: Early versions analyzed entire documents or sections, often missing multiple distinct risks within a single paragraph. We iterated to a more granular section-based analysis with a multi-label classification approach, significantly improving the depth of the AI's findings.
Rule Engine Nuance: Simple keyword searches proved insufficient. We evolved the rules engine to be context-aware (e.g., dynamic APR checks) and to handle edge cases like optional clauses (e.g., ignoring "lump sum" if it was an unselected option).
📚 Data Sources
The test suite of PDF documents used for development and validation (standard and predatory agreements for various loan types) was manually created for this project. This was done to ensure a diverse and challenging set of test cases that accurately reflect both fair and predatory lending practices, providing a reliable benchmark for the system's accuracy.
💡 Future Work
Fine-tuning on Legal Text: Fine-tune a specialized language model (like a legal-BERT) on a corpus of legal and financial documents to improve its contextual understanding.
User-Provided Context: Allow users to optionally provide their income level to enable more personalized flags (e.g., "This monthly payment represents over 40% of your stated monthly income").
Historical Analysis: Allow users to track changes between different versions of a loan document to easily spot newly introduced risky clauses.
Explanation Expansion: For each flag, provide links to external resources (like the CFPB or NCLC) that explain the risk in greater detail.
👨‍💻 Team
Gurkirat Gill