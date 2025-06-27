import streamlit as st
import requests
import os
from typing import List, Dict, Tuple, Any

# ==============================================================================
# --- AI CONFIGURATION ---
# ==============================================================================

MODEL_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

CANDIDATE_LABELS = [
    "Clause describing a severe penalty or repossession",
    "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer",
    "Clause describing a prepayment penalty",
    "Clause encouraging a debt cycle (e.g., rollover or renewal)",
    "Clause about standard late payment fees",
    "Standard clause about loan terms and interest rates",
    "Normal informational clause about parties or governing law",
]

PREDATORY_LABELS = {
    "Clause describing a severe penalty or repossession",
    "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer",
    "Clause describing a prepayment penalty",
    "Clause encouraging a debt cycle (e.g., rollover or renewal)",
}

LABEL_TO_CONCEPT_MAP = {
    "Clause describing a severe penalty or repossession": {"title": "Severe Penalty / Repossession", "id": "AGGRESSIVE_COLLECTION"},
    "Clause containing a hidden or unusual fee": {"title": "Hidden or Unusual Fee", "id": "HIDDEN_FEE"},
    "High-pressure sales tactic or time-limited offer": {"title": "High-Pressure Tactic", "id": "HIGH_PRESSURE_TACTIC"},
    "Clause describing a prepayment penalty": {"title": "Prepayment Penalty", "id": "PREPAYMENT_PENALTY"},
    "Clause encouraging a debt cycle (e.g., rollover or renewal)": {"title": "Debt Cycle Encouragement", "id": "LOAN_RENEWAL_ROLLOVER_CLAUSE"},
}

CONFIDENCE_THRESHOLD = 0.60  # 60%

# ==============================================================================
# --- API HELPER FUNCTION ---
# ==============================================================================

#@st.cache_data
def _query_hf_api(text_to_classify: str) -> Dict[str, Any]:
    """
    Sends text to the Hugging Face Inference API for zero-shot classification.

    Args:
        text_to_classify: The text (e.g., a document section) to be analyzed.

    Returns:
        A dictionary containing the API's response, or an empty dictionary on error.
    """
    api_token = None
    try:
        api_token = st.secrets["HF_TOKEN"]
    except (AttributeError, KeyError):
        api_token = os.environ.get("HF_TOKEN")
    if not api_token:
        st.error("Hugging Face API token not found. Please set HF_TOKEN in secrets or environment.")
        return {}
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": text_to_classify, "parameters": {"candidate_labels": CANDIDATE_LABELS}}
    try:
        response = requests.post(MODEL_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"AI analysis unavailable: {e}")
        return {}

# ==============================================================================
# --- MAIN AI ENGINE FUNCTION ---
# ==============================================================================

def run_ai_analysis(sections: List[str], max_sections: int = 10) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Analyzes document sections using the AI model and generates a risk score.
    """
    total_risk_score = 0
    all_flags = []

    for section_text in sections[:max_sections]:
        if len(section_text.split()) < 5:
            continue

        ai_result = _query_hf_api(section_text)

        if ai_result and 'labels' in ai_result and 'scores' in ai_result:
            top_label = ai_result['labels'][0]
            top_score = ai_result['scores'][0]

            if top_label in PREDATORY_LABELS and top_score > CONFIDENCE_THRESHOLD:
                
                score_to_add = 10
                if top_score > 0.90: score_to_add = 25
                elif top_score > 0.80: score_to_add = 15
                
                total_risk_score += score_to_add

                concept_info = LABEL_TO_CONCEPT_MAP.get(top_label, {"title": "Potential Risk", "id": "AI_UNKNOWN_RISK"})
                
                flag = {
                    "type": "error" if top_score > 0.90 else "warning",
                    "title": f"AI Analysis: {concept_info['title']}",
                    "explanation": f"The AI model flagged this section as a potential '{top_label}' with {top_score:.0%} confidence.",
                    "context": section_text,
                    "concept_id": concept_info['id'],  # ADDED THIS LINE
                    "source": "ai"  # Identify the source
                }
                all_flags.append(flag)

    return total_risk_score, all_flags