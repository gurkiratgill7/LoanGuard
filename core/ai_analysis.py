# core/ai_analysis.py

import streamlit as st
import requests
from typing import List, Dict, Tuple, Any

# ==============================================================================
# --- AI CONFIGURATION ---
# ==============================================================================

# The specific zero-shot classification model we will use from Hugging Face.
MODEL_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

# These are the categories we will ask the AI to classify each section into.
# They are written as descriptive phrases to give the model better context.
CANDIDATE_LABELS = [
    "Clause describing a severe penalty or repossession",
    "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer",
    "Clause describing a prepayment penalty",
    "Clause about standard late payment fees",
    "Standard clause about loan terms and interest rates",
    "Normal informational clause about parties or governing law",
]

# We define which of the above labels we consider to be predatory or high-risk.
PREDATORY_LABELS = {
    "Clause describing a severe penalty or repossession",
    "Clause containing a hidden or unusual fee",
    "High-pressure sales tactic or time-limited offer",
    "Clause describing a prepayment penalty",
}

# The confidence threshold below which we ignore the AI's classification.
CONFIDENCE_THRESHOLD = 0.60 # 60%


# ==============================================================================
# --- API HELPER FUNCTION ---
# ==============================================================================

def _query_hf_api(text_to_classify: str) -> Dict[str, Any]:
    """
    Sends text to the Hugging Face Inference API for zero-shot classification.

    Args:
        text_to_classify: The text (e.g., a document section) to be analyzed.

    Returns:
        A dictionary containing the API's response, or an empty dictionary on error.
    """
    try:
        # Securely fetch the API token from Streamlit secrets.
        api_token = st.secrets["HF_API_TOKEN"]
    except KeyError:
        st.error("Hugging Face API token not found. Please set HF_API_TOKEN in your Streamlit secrets.")
        return {}

    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        "inputs": text_to_classify,
        "parameters": {"candidate_labels": CANDIDATE_LABELS},
    }
    
    try:
        response = requests.post(MODEL_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        # In a real app, you might want to show a warning to the user
        # st.warning("AI analysis is temporarily unavailable due to a network issue.")
        return {}


# ==============================================================================
# --- MAIN AI ENGINE FUNCTION ---
# ==============================================================================

def run_ai_analysis(sections: List[str]) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Analyzes document sections using the AI model and generates a risk score.

    Args:
        sections: A list of strings, where each string is a document section.

    Returns:
        A tuple containing the total AI risk score and a list of AI-generated flags.
    """
    total_risk_score = 0
    all_flags = []

    for section_text in sections:
        # Don't analyze very short, uninteresting sections.
        if len(section_text.split()) < 5:
            continue

        ai_result = _query_hf_api(section_text)

        # Check if the API call was successful and returned a valid result
        if ai_result and 'labels' in ai_result and 'scores' in ai_result:
            top_label = ai_result['labels'][0]
            top_score = ai_result['scores'][0]

            # Only consider the result if it's a predatory label AND above our confidence threshold
            if top_label in PREDATORY_LABELS and top_score > CONFIDENCE_THRESHOLD:
                
                # Add score based on how confident the AI is
                if top_score > 0.90:
                    score_to_add = 25
                elif top_score > 0.80:
                    score_to_add = 15
                else: # 60-80% confidence
                    score_to_add = 10
                
                total_risk_score += score_to_add

                # Create a flag to be displayed in the UI
                flag = {
                    "type": "warning",
                    "title": f"AI Flag: Possible {top_label.split(' ')[2].capitalize()} Clause",
                    "explanation": f"The AI model identified this section as a potential '{top_label}' with {top_score:.0%} confidence. Please review it carefully.",
                    "context": section_text # Provide the full section as context
                }
                all_flags.append(flag)

    return total_risk_score, all_flags