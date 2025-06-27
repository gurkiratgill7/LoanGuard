# core/rule_analysis.py

import re
from typing import List, Dict, Tuple, Any, Literal, Set

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

LoanType = Literal["Mortgage", "Car Loan", "Personal Loan", "Student Loan", "Payday Loan", "Unknown"]

# Dictionaries for Rules with Standardized `concept_id`s
# Red Flags: Predatory or consumer-unfriendly clauses
KEYWORD_SCORES = {
    r'rollover': {"score": 25, "title": "Loan Rollover Clause", "concept_id": "ROLLOVER"},
    r'renew(al|ed)?': {"score": 25, "title": "Loan Renewal/Rollover Clause", "concept_id": "ROLLOVER"},
    r'wage garnishment': {"score": 20, "title": "Aggressive Collection: Wage Garnishment", "concept_id": "WAGE_GARNISHMENT"},
    r'repossession': {"score": 20, "title": "Aggressive Collection: Repossession", "concept_id": "REPOSSESSION"},
    r'prepayment penalty': {"score": 20, "title": "Prepayment Penalty", "concept_id": "PREPAYMENT_PENALTY"},
    r'balloon payment': {"score": 20, "title": "Balloon Payment Clause", "concept_id": "BALLOON_PAYMENT"},
    r'binding arbitration': {"score": 10, "title": "Mandatory Arbitration Clause", "concept_id": "ARBITRATION"},
    r'adjustable rate': {"score": 15, "title": "Adjustable (Variable) Rate", "concept_id": "ADJUSTABLE_RATE"},
    r'variable rate': {"score": 15, "title": "Variable (Adjustable) Rate", "concept_id": "ADJUSTABLE_RATE"},
    r'lump sum': {"score": 10, "title": "Lump Sum Repayment", "concept_id": "LUMP_SUM"},
}

# Red Flags: Vague or ambiguous terms
AMBIGUOUS_TERMS = {
    r'at our sole discretion': {"score": 10, "title": "Ambiguous Clause: 'Sole Discretion'", "concept_id": "AMBIGUITY"},
    r'subject to change without notice': {"score": 15, "title": "Ambiguous Clause: 'Subject to Change'", "concept_id": "AMBIGUITY"},
    r'terms may vary': {"score": 5, "title": "Ambiguous Clause: 'Terms May Vary'", "concept_id": "AMBIGUITY"},
    r'as determined by the lender': {"score": 10, "title": "Ambiguous Clause: 'Determined by Lender'", "concept_id": "AMBIGUITY"},
}

# Green Flags: Pro-consumer clauses that negate a corresponding red flag
CONSUMER_PROTECTIONS = {
    r'\bno prepayment penalty\b': {"title": "No Prepayment Penalty", "concept_id": "PREPAYMENT_PENALTY"},
    r'cooling-off period': {"title": "Cooling-Off Period", "concept_id": "COOLING_OFF"},
    r'right to cancel': {"title": "Right to Cancel", "concept_id": "RIGHT_TO_CANCEL"},
}

FEE_PATTERNS = {
    "Origination Fee": r'origination fee.*?(\$?[\d,\.]+\%?)',
    "Processing Fee": r'processing fee.*?(\$?[\d,\.]+\%?)',
    "Application Fee": r'application.*?fee.*?(\$?[\d,\.]+\%?)',
    "Documentation Fee": r'documentation fee.*?(\$?[\d,\.]+\%?)',
    "Maintenance Fee": r'maintenance fee.*?(\$?[\d,\.]+\%?)',
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

def _check_consumer_protections(text: str) -> Tuple[List[Dict[str, Any]], Set[str]]:
    flags, negated_concepts = [], set()
    for pattern, details in CONSUMER_PROTECTIONS.items():
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({"type": "success", "title": f"Positive Finding: {details['title']}", "explanation": "This is a consumer-friendly term.", "concept_id": details['concept_id']})
            negated_concepts.add(details['concept_id'])
    return flags, negated_concepts

def _check_keywords_and_ambiguity(text: str, negated_concepts: Set[str]) -> Tuple[int, List[Dict[str, Any]]]:
    score, flags, is_optional = 0, [], _is_optional_clause(text)
    combined_risks = {**KEYWORD_SCORES, **AMBIGUOUS_TERMS}
    for pattern, details in combined_risks.items():
        if details['concept_id'] in negated_concepts: continue
        if re.search(pattern, text, re.IGNORECASE):
            if "lump sum" in pattern and is_optional: continue
            score += details["score"]
            flag_type = "error" if details["score"] >= 20 else "warning"
            flags.append({"type": flag_type, "title": details["title"], "explanation": f"The phrase '{pattern}' was found, which can be a risk indicator.", "concept_id": details['concept_id'], "score": details["score"]})
    return score, flags

def _check_apr(text: str, loan_type: LoanType) -> Tuple[int, List[Dict[str, Any]]]:
    score, flags, thresholds = 0, [], APR_THRESHOLDS[loan_type]
    apr_patterns = [r'rate of\s*(\d+\.?\d*)\s*%', r'apr\s*(?:of|is)\s*(\d+\.?\d*)%?', r'annual percentage rate\s*(?:of|is)\s*(\d+\.?\d*)%?']
    for pattern in apr_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            apr = _extract_number(match.group(1))
            title, explanation, flag_type, points = "", "", "info", 0
            if apr > thresholds["predatory"]:
                points, title, explanation, flag_type = 50, f"Critically High APR: {apr}%", f"An APR of {apr}% is predatory for a {loan_type}.", "error"
            elif apr > thresholds["very_high"]:
                points, title, explanation, flag_type = 25, f"Very High APR: {apr}%", f"This APR is exceptionally high for a {loan_type}.", "error"
            elif apr > thresholds["high"]:
                points, title, explanation, flag_type = 10, f"High APR: {apr}%", f"This APR is higher than average for a {loan_type}.", "warning"
            if title:
                score += points
                flags.append({"type": flag_type, "title": title, "explanation": explanation, "score": points})
            return score, flags
    return score, flags

def _check_late_fees(text: str) -> Tuple[int, List[Dict[str, Any]]]:
    score, flags = 0, [],
    match = re.search(r'(late fee|late charge|late payment penalty).*?\$?(\d+\.?\d*).*?after (\d+)\s*days', text, re.IGNORECASE)
    if match:
        fee_amount, grace_period = _extract_number(match.group(2)), int(match.group(3))
        if grace_period < 10:
            points = 10
            score += points
            flags.append({"type": "warning", "title": "Short Grace Period for Late Fee", "explanation": f"A grace period of only {grace_period} days is very short.", "score": points})
        if fee_amount > 50:
            points = 5
            score += points
            flags.append({"type": "warning", "title": f"High Late Fee Amount: ${fee_amount}", "explanation": "The late fee amount is substantial.", "score": points})
    return score, flags

def _check_short_term(text: str, loan_type: LoanType) -> Tuple[int, List[Dict[str, Any]]]:
    score, flags = 0, []
    match = re.search(r'due in (\d+)\s*days|(\d+)\s*day term|next payday', text, re.IGNORECASE)
    if match:
        days_str = match.group(1) or match.group(2)
        days = int(days_str) if days_str else 14
        points = 0
        if days < 30:
            points = 30 if loan_type == "Payday Loan" else 15
            score += points
            flags.append({"type": "error", "title": f"Very Short Repayment Term: {days} days", "explanation": f"A repayment period this short is a major red flag, especially for a {loan_type}.", "score": points})
        elif days < 90:
            points = 10
            score += points
            flags.append({"type": "warning", "title": f"Short Repayment Term: {days} days", "explanation": f"A repayment period of {days} days is shorter than standard.", "score": points})
    return score, flags

def _check_fee_burden(full_text: str, loan_amount: float) -> Tuple[int, List[Dict[str, Any]]]:
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
        points = 0
        if fee_ratio > 8:
            points, title, explanation, flag_type = 30, "Excessive Fee Burden", f"Upfront fees total ${total_fees:,.2f} ({fee_ratio:.1f}% of loan), a major red flag.", "error"
        elif fee_ratio > 5:
            points, title, explanation, flag_type = 15, "High Fee Burden", f"Upfront fees total ${total_fees:,.2f} ({fee_ratio:.1f}% of loan), which is high.", "warning"
        if points > 0:
            score += points
            flags.append({"type": flag_type, "title": title, "explanation": explanation, "score": points})
    return score, flags


# ==============================================================================
# --- MAIN ENGINE FUNCTION ---
# ==============================================================================

def run_rules_engine(sections: List[str], full_text: str) -> Tuple[int, List[Dict[str, Any]]]:
    """Analyzes document sections with a two-pass system to avoid contradictions."""
    all_flags = []

    # --- Step 1: Global Analysis (run once on full text) ---
    loan_type = _identify_loan_type(full_text)
    loan_amount = _extract_loan_amount(full_text)
    all_flags.append({"type": "info", "title": f"Detected Loan Type: {loan_type}", "explanation": "Risk analysis is adjusted for this loan type."})
    score, flags = _check_fee_burden(full_text, loan_amount)
    all_flags.extend(flags)

    # --- Step 2: Section-by-Section Two-Pass Analysis ---
    for section_text in sections:
        green_flags, negated_concepts = _check_consumer_protections(section_text)
        all_flags.extend(green_flags)
        
        check_functions = [
            (_check_apr, [section_text, loan_type]),
            (_check_late_fees, [section_text]),
            (_check_short_term, [section_text, loan_type]),
            (_check_keywords_and_ambiguity, [section_text, negated_concepts])
        ]
        
        for func, args in check_functions:
            score, flags = func(*args)
            all_flags.extend(flags)

    # --- Step 3: De-duplicate and Finalize ---
    unique_flags = []
    seen_titles = set()
    for flag in all_flags:
        if flag['title'] not in seen_titles:
            unique_flags.append(flag)
            seen_titles.add(flag['title'])
    
    total_risk_score = sum(f.get('score', 0) for f in unique_flags)
            
    return total_risk_score, unique_flags