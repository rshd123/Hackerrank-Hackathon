import sys
sys.path.insert(0, ".")

import pandas as pd
from datetime import datetime
from code.data_loader import DataLoader, Request
from code.financial_state import FinancialState
from code.forecaster import Forecaster
from code.plan_generator import PlanGenerator
from code.decision import DecisionEngine

d = DataLoader("dataset/")
profiles = d.load_profiles()
sample = pd.read_csv("dataset/sample_requests.csv")

print("Comparing our engine output vs sample ground truth")
print("=" * 80)

matches = 0
mismatches = 0

for _, row in sample.iterrows():
    rid = row["request_id"]
    uid = row["user_id"]

    req = Request(
        request_id=rid,
        user_id=uid,
        request_date=datetime.strptime(row["request_date"], "%Y-%m-%d").date(),
        request_type=row["request_type"],
        requested_amount=row["requested_amount"],
        desired_completion_date=(
            datetime.strptime(str(row["desired_completion_date"]), "%Y-%m-%d").date()
            if pd.notna(row["desired_completion_date"]) else None
        ),
        allows_partial_payment=bool(row["allows_partial_payment"]),
        request_text=row.get("request_text", ""),
    )

    p = profiles.get(uid)
    if not p:
        print(f"{rid}: NO PROFILE")
        continue

    evts = d.load_events(uid)
    st = FinancialState(p, evts, d)
    fc = Forecaster(st, req)
    gn = PlanGenerator(st, req, d)
    cands = gn.generate_all_candidates()
    eng = DecisionEngine(fc)
    dec = eng.decide(cands)

    gt_status = row["affordability_status"]
    gt_method = row["recommended_payment_method"]
    gt_amount = row["amount_safe_to_pay"]

    our_status = dec.affordability_status
    our_method = dec.recommended_payment_method
    our_amount = dec.amount_safe_to_pay

    status_match = our_status == gt_status
    method_match = our_method == gt_method

    if status_match and method_match:
        matches += 1
        mark = "PASS"
    else:
        mismatches += 1
        mark = "FAIL"

    print(f"\n{rid}: {mark}")
    if not status_match:
        print(f"  Status: GT={gt_status}, ours={our_status}")
    if not method_match:
        print(f"  Method: GT={gt_method}, ours={our_method}")
    print(f"  Amount safe: GT={gt_amount}, ours={our_amount:.2f}")
    print(f"  Plan GT: {str(row['payment_plan'])[:60]}")
    print(f"  Plan ours: {dec.payment_plan[:60]}")

print(f"\n{'=' * 80}")
print(f"Results: {matches} match, {mismatches} mismatch out of {len(sample)}")
print(f"Accuracy: {matches / len(sample) * 100:.1f}%")
