# core/rules.py

import re
from typing import List, Dict, Tuple, Any, Literal

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

LoanType = Literal["Mortgage", "Car Loan", "Personal Loan", "Student Loan", "Payday Loan", "Unknown"]

# --- Risk Scoring Dictionaries ---

# Using more flexible regex for keywords where appropriate
KEYWORD_SCORES = {
    r'rollover': {"score": 25, "title": "Loan Rollover Clause"},
    r'renew(al|ed)?': {"score": 25, "title": "Loan Renewal/Rollover Clause"}, # Matches renew, renewal, renewed
    r'wage garnishment': {"score": 20, "title": "Aggressive Collection: Wage Garnishment"},
    r'repossession': {"score": 20, "title": "Aggressive Collection: Repossession"},
    r'prepayment penalty': {"score": 20, "title": "Prepayment Penalty"},
    r'balloon payment': {"score": 20, "title": "Balloon Payment Clause"},
    r'binding arbitration': {"score": 10, "title": "Mandatory Arbitration Clause"},
    r'adjustable rate': {"score": 15, "title": "Adjustable (Variable) Rate"},
    r'variable rate': {"score": 15, "title": "Variable (Adjustable) Rate"},
    r'lump sum': {"score": 10, "title": "Lump Sum Repayment"},
}

AMBIGUOUS_TERMS = {
    r'at our sole discretion': {"score": 10, "title": "Ambiguous Clause: 'Sole Discretion'"},
    r'subject to change without notice': {"score": 15, "title": "Ambiguous Clause: 'Subject to Change'"},
    r'terms may vary': {"score": 5, "title": "Ambiguous Clause: 'Terms May Vary'"},
    r'as determined by the lender': {"score": 10, "title": "Ambiguous Clause: 'Determined by Lender'"},
}

FEE_PATTERNS = {
    "Origination Fee": r'origination fee.*?(\$?[\d,\.]+\%?)',
    "Processing Fee": r'processing fee.*?(\$?[\d,\.]+\%?)',
    "Application Fee": r'application.*?fee.*?(\$?[\d,\.]+\%?)',
    "Documentation Fee": r'documentation fee.*?(\$?[\d,\.]+\%?)',
    "Maintenance Fee": r'maintenance fee.*?(\$?[\d,\.]+\%?)',
}

CONSUMER_PROTECTIONS = {
    r'\bno prepayment penalty\b': "No Prepayment Penalty",
    r'cooling-off period': "Cooling-Off Period",
    r'right to cancel': "Right to Cancel",
}

APR_THRESHOLDS = {
    "Mortgage": {"high": 10, "very_high": 15, "predatory": 25},
    "Car Loan": {"high": 15, "very_high": 21, "predatory": 36},
    "Student Loan": {"high": 12, "very_high": 18, "predatory": 36},
    "Personal Loan": {"high": 25, "very_high": 36, "predatory": 100},
    "Payday Loan": {"high": 100, "very_high": 300, "predatory": 500},
    "Unknown": {"high": 20, "very_high": 36, "predatory": 100}
}


# ==============================================================================
# --- HELPER FUNCTIONS ---
# ==============================================================================

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
    text_lower = full_text.lower()
    if "mortgage" in text_lower: return "Mortgage"
    if "car loan" in text_lower or "auto loan" in text_lower: return "Car Loan"
    if "payday loan" in text_lower: return "Payday Loan"
    if "student loan" in text_lower: return "Student Loan"
    if "personal loan" in text_lower or "home equity" in text_lower: return "Personal Loan"
    return "Unknown"


# ==============================================================================
# --- RULE-CHECKING FUNCTIONS ---
# ==============================================================================

def _check_apr(text: str, loan_type: LoanType) -> Tuple[int, List[Dict[str, Any]]]:
    """Dynamically checks for high APRs using multiple robust patterns."""
    score, flags, thresholds = 0, [], APR_THRESHOLDS[loan_type]
    
    apr_patterns = [
        r'rate of\s*(\d+\.?\d*)\s*%',
        r'apr\s*(?:of|is)\s*(\d+\.?\d*)%?',
        r'annual percentage rate\s*(?:of|is)\s*(\d+\.?\d*)%?',
        r'(\d+\.?\d*)\s*percent(?:age rate)?'
    ]
    
    for pattern in apr_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            apr = _extract_number(match.group(1))
            title, explanation, flag_type = "", "", "info"
            if apr > thresholds["predatory"]:
                score, title, explanation, flag_type = 50, f"Critically High APR: {apr}%", f"An APR of {apr}% is considered predatory for a {loan_type}.", "error"
            elif apr > thresholds["very_high"]:
                score, title, explanation, flag_type = 25, f"Very High APR: {apr}%", f"This APR is exceptionally high for a {loan_type}.", "error"
            elif apr > thresholds["high"]:
                score, title, explanation, flag_type = 10, f"High APR: {apr}%", f"This APR is higher than average for a {loan_type}.", "warning"
            if title: flags.append({"type": flag_type, "title": title, "explanation": explanation})
            return score, flags # Return after the first match to avoid multiple APR flags
    return score, flags

def _check_late_fees(text: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Checks for aggressive late fee terms with a more robust regex."""
    score, flags = 0, []
    # Enhanced regex to catch more variations
    match = re.search(r'(late fee|late charge|late payment penalty).*?\$?(\d+\.?\d*).*?after (\d+)\s*days', text, re.IGNORECASE)
    if match:
        fee_amount, grace_period = _extract_number(match.group(2)), int(match.group(3))
        if grace_period < 10:
            score += 10
            flags.append({"type": "warning", "title": "Short Grace Period for Late Fee", "explanation": f"A grace period of only {grace_period} days is very short."})
        if fee_amount > 50:
            score += 5
            flags.append({"type": "warning", "title": f"High Late Fee Amount: ${fee_amount}", "explanation": "The late fee amount is substantial."})
    return score, flags

def _check_short_term(text: str, loan_type: LoanType) -> Tuple[int, List[Dict[str, Any]]]:
    """Reintroduced check for short repayment terms, critical for payday loans."""
    score, flags = 0, []
    match = re.search(r'due in (\d+)\s*days|(\d+)\s*day term|next payday', text, re.IGNORECASE)
    if match:
        days_str = match.group(1) or match.group(2)
        days = int(days_str) if days_str else 14 # Assume 'next payday' is 14 days
        
        if days < 30:
            score += 30 if loan_type == "Payday Loan" else 15
            flags.append({"type": "error", "title": f"Very Short Repayment Term: {days} days", "explanation": f"A repayment period this short is a major red flag, especially for a {loan_type}, and can lead to a debt cycle."})
        elif days < 90:
            score += 10
            flags.append({"type": "warning", "title": f"Short Repayment Term: {days} days", "explanation": f"A repayment period of {days} days is shorter than standard for most loans."})
    return score, flags

def _check_keywords_and_ambiguity(text: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Checks for risky keywords and ambiguous phrases using flexible regex."""
    score, flags, is_optional = 0, [], _is_optional_clause(text)
    combined_risks = {**KEYWORD_SCORES, **AMBIGUOUS_TERMS}
    for pattern, details in combined_risks.items():
        if re.search(pattern, text, re.IGNORECASE):
            # Special handling for 'lump sum' option
            if "lump sum" in pattern and is_optional: continue
            
            score += details["score"]
            flag_type = "error" if details["score"] >= 20 else "warning"
            flags.append({"type": flag_type, "title": details["title"], "explanation": f"The phrase '{pattern}' was found, which can be a risk indicator."})
    return score, flags

def _check_fee_burden(full_text: str, loan_amount: float) -> Tuple[int, List[Dict[str, Any]]]:
    """Calculates the total fee burden as a percentage of the loan amount."""
    if loan_amount == 0: return 0, []
    total_fees, flags, score = 0, [], 0
    for fee_name, pattern in FEE_PATTERNS.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            fee_value_str = match.group(1)
            fee_amount = (_extract_number(fee_value_str) / 100) * loan_amount if "%" in fee_value_str else _extract_number(fee_value_str)
            total_fees += fee_amount
            flags.append({"type": "info", "title": f"Identified Fee: {fee_name}", "explanation": f"Found a fee of ${fee_amount:,.2f}."})
    if total_fees > 0:
        fee_ratio = (total_fees / loan_amount) * 100
        if fee_ratio > 8:
            score, title, explanation, flag_type = 30, "Excessive Fee Burden", f"Upfront fees total ${total_fees:,.2f} ({fee_ratio:.1f}% of loan), a major red flag.", "error"
            flags.append({"type": flag_type, "title": title, "explanation": explanation})
        elif fee_ratio > 5:
            score, title, explanation, flag_type = 15, "High Fee Burden", f"Upfront fees total ${total_fees:,.2f} ({fee_ratio:.1f}% of loan), which is high.", "warning"
            flags.append({"type": flag_type, "title": title, "explanation": explanation})
    return score, flags

def _check_consumer_protections(text: str) -> List[Dict[str, Any]]:
    """Identifies pro-consumer clauses ('green flags')."""
    flags = []
    for pattern, title in CONSUMER_PROTECTIONS.items():
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({"type": "success", "title": f"Positive Finding: {title}", "explanation": "This is a consumer-friendly term."})
    return flags


# ==============================================================================
# --- MAIN ENGINE FUNCTION ---
# ==============================================================================

def run_rules_engine(sections: List[str], full_text: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Analyzes document sections against a comprehensive set of rules."""
    total_risk_score = 0
    all_flags = []

    # --- Step 1: Global Analysis (run once on full text) ---
    loan_type = _identify_loan_type(full_text)
    loan_amount = _extract_loan_amount(full_text)
    all_flags.append({"type": "info", "title": f"Detected Loan Type: {loan_type}", "explanation": "Risk analysis is adjusted for this loan type."})
    score, flags = _check_fee_burden(full_text, loan_amount)
    total_risk_score += score
    all_flags.extend(flags)

    # --- Step 2: Section-by-Section Analysis ---
    for section_text in sections:
        # Combine all check functions for cleaner iteration
        check_functions = [
            (_check_apr, [section_text, loan_type]),
            (_check_late_fees, [section_text]),
            (_check_short_term, [section_text, loan_type]),
            (_check_keywords_and_ambiguity, [section_text]),
            (_check_consumer_protections, [section_text])
        ]
        for func, args in check_functions:
            result = func(*args)
            if isinstance(result, tuple): # Functions that return (score, flags)
                score, flags = result
                total_risk_score += score
                all_flags.extend(flags)
            else: # Functions that only return flags (e.g., green flags)
                all_flags.extend(result)

    # --- Step 3: De-duplicate and Finalize ---
    unique_flags = []
    seen_titles = set()
    for flag in all_flags:
        if flag['title'] not in seen_titles:
            unique_flags.append(flag)
            seen_titles.add(flag['title'])
            
    return total_risk_score, unique_flags