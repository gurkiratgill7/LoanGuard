# core/rules.py

import re
from typing import List, Dict, Tuple, Any, Literal

# --- Configuration for the Rules Engine ---
# (KEYWORD_SCORES dictionary remains the same as before)
KEYWORD_SCORES = {
    # High-risk (often exclusively predatory)
    "rollover": {"score": 25, "title": "Loan Rollover Clause"},
    "renew": {"score": 25, "title": "Loan Renewal/Rollover Clause"},
    "wage garnishment": {"score": 20, "title": "Aggressive Collection Tactic"},
    "repossession": {"score": 20, "title": "Aggressive Collection Tactic (Repossession)"},
    "prepayment penalty": {"score": 20, "title": "Prepayment Penalty"},
    # Medium-risk (consumer-unfriendly)
    "binding arbitration": {"score": 10, "title": "Mandatory Arbitration Clause"},
    "adjustable rate": {"score": 15, "title": "Adjustable (Variable) Rate"},
    "variable rate": {"score": 15, "title": "Variable (Adjustable) Rate"},
    "lump sum": {"score": 10, "title": "Lump Sum Repayment"},
    # Lower-risk but worth noting
    "late fee": {"score": 5, "title": "Late Fee Clause"},
    "late payment": {"score": 5, "title": "Late Payment Clause"},
    "processing fee": {"score": 5, "title": "Processing Fee"},
    "origination fee": {"score": 5, "title": "Origination Fee"},
}

# --- NEW: Configuration for Dynamic APR ---
LoanType = Literal["Mortgage", "Car Loan", "Personal Loan", "Student Loan", "Payday Loan", "Unknown"]

APR_THRESHOLDS = {
    "Mortgage": {"high": 10, "very_high": 15, "predatory": 25},
    "Car Loan": {"high": 15, "very_high": 21, "predatory": 36},
    "Student Loan": {"high": 12, "very_high": 18, "predatory": 36},
    "Personal Loan": {"high": 25, "very_high": 36, "predatory": 100},
    "Payday Loan": {"high": 100, "very_high": 300, "predatory": 500},
    "Unknown": {"high": 20, "very_high": 36, "predatory": 100} # Default fallback
}

# --- Helper Functions ---
# (_extract_number, _extract_loan_amount, _is_optional_clause remain the same)

def _extract_number(text: str) -> float:
    text = text.replace(",", "").replace("$", "").replace("%", "")
    match = re.search(r'(\d+\.?\d*)', text)
    if match: return float(match.group(1))
    return 0.0

def _extract_loan_amount(full_text: str) -> float:
    match = re.search(r'(?:loan amount|borrowed)\s*(?:of|is)?\s*\$?([\d,]+\.?\d*)', full_text, re.IGNORECASE)
    if match: return _extract_number(match.group(1))
    return 0.0

def _is_optional_clause(text: str) -> bool:
    text_lower = text.lower()
    if "check one" in text_lower or "☐" in text: return True
    return False

def _identify_loan_type(full_text: str) -> LoanType:
    """Classifies the loan type based on keywords in the text."""
    text_lower = full_text.lower()
    if "mortgage" in text_lower:
        return "Mortgage"
    if "car loan" in text_lower or "auto loan" in text_lower:
        return "Car Loan"
    if "payday loan" in text_lower:
        return "Payday Loan"
    if "student loan" in text_lower:
        return "Student Loan"
    if "personal loan" in text_lower or "home equity" in text_lower:
        return "Personal Loan"
    return "Unknown"


# --- Rule-Checking Functions ---

def _check_apr(text: str, loan_type: LoanType) -> Tuple[int, List[Dict[str, Any]]]:
    """Dynamically checks for high APRs based on the loan type."""
    score = 0
    flags = []
    thresholds = APR_THRESHOLDS[loan_type]

    matches = re.finditer(r'rate of\s*(\d+\.?\d*)\s*%', text, re.IGNORECASE)
    for match in matches:
        apr = _extract_number(match.group(1))
        title = ""
        explanation = ""
        flag_type = "info" # Default
        
        if apr > thresholds["predatory"]:
            score += 50
            title = f"Critically High APR for a {loan_type}: {apr}%"
            explanation = f"An APR of {apr}% is considered predatory for this type of loan."
            flag_type = "error"
        elif apr > thresholds["very_high"]:
            score += 25
            title = f"Very High APR for a {loan_type}: {apr}%"
            explanation = f"This APR is exceptionally high compared to the market average for a {loan_type}."
            flag_type = "error"
        elif apr > thresholds["high"]:
            score += 10
            title = f"High APR for a {loan_type}: {apr}%"
            explanation = f"This APR is higher than average for a {loan_type} and will significantly increase the total cost."
            flag_type = "warning"

        if title: # Only add a flag if a threshold was met
            flags.append({"type": flag_type, "title": title, "explanation": explanation})
            
    return score, flags

# (_check_late_fees and _check_keywords functions remain the same)
def _check_late_fees(text: str) -> Tuple[int, List[Dict[str, Any]]]:
    score = 0
    flags = []
    match = re.search(r'late.*?fee of \$?(\d+\.?\d*).*?after (\d+)\s*days', text, re.IGNORECASE)
    if match:
        fee_amount, grace_period = _extract_number(match.group(1)), int(match.group(2))
        if grace_period < 10:
            score += 10
            flags.append({"type": "warning", "title": "Short Grace Period for Late Fee", "explanation": f"A grace period of only {grace_period} days is very short."})
        if fee_amount > 50:
            score += 5
            flags.append({"type": "warning", "title": f"High Late Fee Amount: ${fee_amount}", "explanation": "The late fee amount is substantial."})
    return score, flags

def _check_keywords(text: str) -> Tuple[int, List[Dict[str, Any]]]:
    score = 0
    flags = []
    is_optional = _is_optional_clause(text)
    for keyword, details in KEYWORD_SCORES.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            if is_optional and keyword == "lump sum": continue
            score += details["score"]
            flag_type = "error" if details["score"] >= 20 else "warning"
            flags.append({"type": flag_type, "title": details["title"], "explanation": f"The term '{keyword}' was found, which can be associated with consumer-unfriendly lending practices."})
    return score, flags

# --- Main Engine Function ---

def run_rules_engine(sections: List[str], full_text: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Analyzes document sections against a set of rules."""
    total_risk_score = 0
    all_flags = []

    # --- NEW: Identify loan type once at the beginning ---
    loan_type = _identify_loan_type(full_text)
    # Add a flag to inform the user what we detected
    all_flags.append({"type": "info", "title": f"Detected Loan Type: {loan_type}", "explanation": "The risk analysis has been adjusted for this type of loan."})

    for section_text in sections:
        # Pass loan_type to the APR checker
        apr_score, apr_flags = _check_apr(section_text, loan_type)
        total_risk_score += apr_score
        all_flags.extend(apr_flags)

        # Other checks remain the same
        late_fee_score, late_fee_flags = _check_late_fees(section_text)
        total_risk_score += late_fee_score
        all_flags.extend(late_fee_flags)
        
        keyword_score, keyword_flags = _check_keywords(section_text)
        total_risk_score += keyword_score
        all_flags.extend(keyword_flags)

    # De-duplication logic
    unique_flags = []
    seen_titles = set()
    for flag in all_flags:
        if flag['title'] not in seen_titles:
            unique_flags.append(flag)
            seen_titles.add(flag['title'])

    return total_risk_score, unique_flags