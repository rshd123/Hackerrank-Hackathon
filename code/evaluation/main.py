"""
evaluation/main.py — Validation and scoring scripts

Run this to validate output.csv against sample_requests.csv format.
"""

import csv
from pathlib import Path


def validate_output(output_path):
    """Validate output.csv format and constraints."""
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    required_columns = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation",
    ]
    
    errors = []
    
    # Check columns
    if reader.fieldnames != required_columns:
        errors.append(f"Column mismatch: got {reader.fieldnames}")
    
    valid_statuses = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
    valid_methods = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}
    
    for i, row in enumerate(rows):
        rid = row.get("request_id", f"row_{i}")
        
        # Check amount bounds
        try:
            amt = float(row.get("amount_safe_to_pay", "-1"))
            if amt < 0:
                errors.append(f"{rid}: amount_safe_to_pay < 0")
        except ValueError:
            errors.append(f"{rid}: invalid amount_safe_to_pay")
        
        # Check status
        if row.get("affordability_status") not in valid_statuses:
            errors.append(f"{rid}: invalid affordability_status")
        
        # Check method
        if row.get("recommended_payment_method") not in valid_methods:
            errors.append(f"{rid}: invalid recommended_payment_method")
    
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} errors:")
        for e in errors[:10]:
            print(f"  {e}")
    else:
        print(f"VALIDATION PASSED — {len(rows)} rows, all constraints satisfied")
    
    return len(errors) == 0


if __name__ == "__main__":
    output_path = Path(__file__).parent.parent.parent / "output.csv"
    if output_path.exists():
        validate_output(output_path)
    else:
        print(f"output.csv not found at {output_path}")
