# core/ai_analysis.py

import streamlit as st
from typing import List, Dict, Tuple, Any
from transformers import pipeline, Pipeline

# ==============================================================================
# --- AI CONFIGURATION AND MODEL LOADING (RUNS ONCE AT STARTUP) ---
# ==============================================================================

# This decorator is the key to performance. It loads the model only once.
@st.cache_resource
def load_local_model() -> Pipeline | None:
    """Load the classification model locally and cache it."""
    try:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)
        print("INFO: Local zero-shot classification model loaded successfully.")
        return classifier
    except Exception as e:
        # If model loading fails, show an error in the app.
        st.error(f"Fatal Error: Failed to load local AI model. Please check logs. Error: {e}")
        return None

# Load the model into a global variable when the script is first executed.
CLASSIFIER = load_local_model()

# Your configurations remain the same.
CANDIDATE_LABELS = [
    "Clause describing a severe penalty or repossession", "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer", "Clause describing a prepayment penalty",
    "Clause encouraging a debt cycle (e.g., rollover or renewal)", "Clause with extremely high interest rates or APR",
    "Clause requiring immediate payment or very short terms", "Clause waiving consumer rights or requiring arbitration",
    "Clause about standard late payment fees", "Standard clause about loan terms and interest rates",
    "Normal informational clause about parties or governing law", "Standard clause about payment schedule and amounts",
    "Standard clause about borrower obligations and responsibilities", "Standard clause about loan purpose or use restrictions",
    "Standard clause about insurance or collateral requirements", "Clause allowing early repayment without penalty",
    "Clause providing grace period or payment flexibility", "Clause protecting consumer rights or providing disclosures",
    "Clause offering payment assistance or hardship options", "Clause with competitive interest rates",
    "Clause providing clear terms and transparency",
]
PREDATORY_LABELS = {
    "Clause describing a severe penalty or repossession", "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer", "Clause describing a prepayment penalty",
    "Clause encouraging a debt cycle (e.g., rollover or renewal)", "Clause with extremely high interest rates or APR",
    "Clause requiring immediate payment or very short terms", "Clause waiving consumer rights or requiring arbitration",
}
LABEL_TO_CONCEPT_MAP = {
    "Clause describing a severe penalty or repossession": {"title": "Severe Penalty / Repossession", "id": "AGGRESSIVE_COLLECTION"},
    "Clause containing a hidden or unusual fee": {"title": "Hidden or Unusual Fee", "id": "HIDDEN_FEE"},
    "High-pressure sales tactic or time-limited offer": {"title": "High-Pressure Tactic", "id": "HIGH_PRESSURE_TACTIC"},
    "Clause describing a prepayment penalty": {"title": "Prepayment Penalty", "id": "PREPAYMENT_PENALTY"},
    "Clause encouraging a debt cycle (e.g., rollover or renewal)": {"title": "Debt Cycle Encouragement", "id": "ROLLOVER"},
    "Clause with extremely high interest rates or APR": {"title": "Extremely High Interest Rate", "id": "HIGH_APR"},
    "Clause requiring immediate payment or very short terms": {"title": "Very Short Repayment Term", "id": "SHORT_TERM"},
    "Clause waiving consumer rights or requiring arbitration": {"title": "Waiver of Consumer Rights", "id": "ARBITRATION"},
}
CONFIDENCE_THRESHOLD = 0.60

# ==============================================================================
# --- LOCAL MODEL QUERY FUNCTION ---
# ==============================================================================

def _query_local_model(text_to_classify: str) -> Dict[str, Any]:
    """Uses the pre-loaded local model for classification."""
    # Check if the global model loaded correctly at startup.
    if CLASSIFIER is None:
        return {}
    
    try:
        # No need to load the model again, just use it.
        result = CLASSIFIER(text_to_classify, CANDIDATE_LABELS)
        return result
    except Exception as e:
        print(f"ERROR: Local model inference failed: {e}")
        return {}

# ==============================================================================
# --- MAIN AI ENGINE FUNCTION (Line-by-Line Analysis) ---
# ==============================================================================

def run_ai_analysis(sections: List[str], max_sections: int = 15) -> Tuple[int, List[Dict[str, Any]]]:
    """Analyzes document sections line-by-line using the local AI model."""
    total_risk_score = 0
    all_flags = []

    for section_text in sections[:max_sections]:
        lines = section_text.strip().split('\n')
        if not lines: continue
        
        section_title = lines[0].strip()
        content_lines = [line.strip() for line in lines[1:] if line.strip()]
        
        for line in content_lines:
            if len(line.split()) < 4: continue # Skip very short, uninformative lines
            
            text_to_analyze = f"{section_title}: {line}"
            ai_result = _query_local_model(text_to_analyze)

            if ai_result and 'labels' in ai_result and 'scores' in ai_result:
                # Take only the highest confidence prediction
                top_label = ai_result['labels'][0]
                top_score = ai_result['scores'][0]
                
                if top_label in PREDATORY_LABELS and top_score > CONFIDENCE_THRESHOLD:
                    score_to_add = 10
                    if top_score > 0.90: score_to_add = 25
                    elif top_score > 0.80: score_to_add = 15
                    
                    total_risk_score += score_to_add
                    concept_info = LABEL_TO_CONCEPT_MAP.get(top_label, {"title": "Potential Risk", "id": "AI_UNKNOWN_RISK"})
                    
                    flag = {
                        "type": "warning",
                        "title": f"AI Analysis: {concept_info['title']}",
                        "explanation": f"The AI model flagged this clause as a potential '{top_label}' with {top_score:.0%} confidence.",
                        "context": line,
                        "section": section_title,
                        "concept_id": concept_info['id'],
                        "source": "ai",
                        "score": score_to_add
                    }
                    all_flags.append(flag)

    return total_risk_score, all_flags