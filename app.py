# app.py

import streamlit as st
from core.pdf_to_txt import extract_text_from_pdf, text_to_sections
from core.rule_analysis import run_rules_engine
from core.ai_analysis import run_ai_analysis

# ==============================================================================
# --- PAGE CONFIGURATION ---
# ==============================================================================

# Set the page configuration for a more professional look
st.set_page_config(
    page_title="LoanGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# --- SIDEBAR & DISCLAIMER ---
# ==============================================================================

with st.sidebar:
    st.image("https://i.imgur.com/qgGYj2g.png", width=100) # Placeholder logo
    st.title("About LoanGuard")
    st.info(
        """
        **LoanGuard** is an AI-powered tool designed to help you understand complex loan agreements.
        
        It uses a dual-engine approach:
        1.  **Rule-Based Engine:** Scans for clear red flags like high APRs and predatory keywords.
        2.  **AI Analysis:** Uses a sophisticated NLP model to detect nuanced and contextual risks that rules might miss.
        
        This tool is a proof-of-concept for a hackathon and is for educational purposes only.
        """
    )
    st.warning(
        """
        **Disclaimer:** LoanGuard is not a substitute for professional legal or financial advice. 
        Always consult with a qualified professional before signing any legal document.
        """
    )


# ==============================================================================
# --- MAIN PAGE UI ---
# ==============================================================================

st.title("🛡️ LoanGuard: Your AI-Powered Loan Agreement Analyzer")
st.markdown("Upload a loan agreement in PDF format to scan it for predatory clauses and hidden risks.")

# Create the file uploader widget
uploaded_file = st.file_uploader(
    "Choose a PDF file to analyze",
    type="pdf",
    help="Upload your loan agreement, credit card terms, or any financial contract."
)

if uploaded_file is not None:
    # Add a button to trigger the analysis
    if st.button("Analyze Document", type="primary", use_container_width=True):
        
        # --- ANALYSIS PIPELINE ---
        with st.spinner("Analyzing document... This may take a moment for the AI to process."):
            # Step 1: Extract text and sections from the PDF
            pdf_bytes = uploaded_file.read()
            full_text = extract_text_from_pdf(pdf_bytes)
            
            if not full_text:
                st.error("Could not extract text from the PDF. The file might be empty, corrupted, or image-based.")
                st.stop()
         
            sections = text_to_sections(full_text)

            # Step 2: Run both analysis engines
            rule_score, rule_flags = run_rules_engine(sections, full_text)
            ai_score, ai_flags = run_ai_analysis(sections)


            # Check if AI analysis failed completely (no API responses)
            ai_analysis_failed = (ai_score == 0 and len(ai_flags) == 0)
            
            if ai_analysis_failed:
                # Double the rule score to compensate for missing AI analysis
                adjusted_rule_score = rule_score * 2
                total_score = adjusted_rule_score
                all_flags = rule_flags
                
                # Add warning about AI analysis failure
                st.warning(
                    "⚠️ **AI analysis is unavailable due to API limits being reached.** "
                    "The following score is based solely on rule-based analysis and has been "
                    "doubled to accommodate the lack of AI analysis.", 
                    icon="🤖"
                )
            else:
                # Normal operation - combine both scores
                total_score = rule_score + ai_score
                all_flags = rule_flags + ai_flags

            # Step 3: Combine the results

        # --- DISPLAY RESULTS ---
        st.header("Analysis Report")
        
        # Determine overall risk level and display a summary
        risk_level = "Low"
        if total_score > 60:
            risk_level = "High"
            st.error(f"**Overall Risk: {risk_level}** (Score: {total_score})", icon="🚨")
        elif total_score > 30:
            risk_level = "Medium"
            st.warning(f"**Overall Risk: {risk_level}** (Score: {total_score})", icon="⚠️")
        else:
            risk_level = "Low"
            st.success(f"**Overall Risk: {risk_level}** (Score: {total_score})", icon="✅")

        st.markdown("---")
        
        # Filter flags by type for organized display
        green_flags = [f for f in all_flags if f['type'] == 'success']
        info_flags = [f for f in all_flags if f['type'] == 'info']
        warning_flags = [f for f in all_flags if f['type'] == 'warning']
        error_flags = [f for f in all_flags if f['type'] == 'error']

        # Display organized flags in expandable sections
        if green_flags:
            with st.expander(f"✅ Positive Findings ({len(green_flags)})", expanded=True):
                for flag in green_flags:
                    st.markdown(f"**{flag['title']}**: {flag['explanation']}")
        
        if error_flags:
            with st.expander(f"🚨 Critical Risks Found ({len(error_flags)})", expanded=True):
                for flag in error_flags:
                    st.markdown(f"**{flag['title']}**: {flag['explanation']}")
                    if 'context' in flag:
                        st.code(flag['context'], language=None)
        
        if warning_flags:
            with st.expander(f"⚠️ Potential Warnings ({len(warning_flags)})", expanded=False):
                for flag in warning_flags:
                    st.markdown(f"**{flag['title']}**: {flag['explanation']}")
                    if 'context' in flag:
                        st.code(flag['context'], language=None)

        if info_flags:
            with st.expander(f"ℹ️ Informational Notes ({len(info_flags)})", expanded=False):
                 for flag in info_flags:
                    st.markdown(f"**{flag['title']}**: {flag['explanation']}")