import sys
sys.path.insert(0, ".")

import os
import pandas as pd
from datetime import datetime
from code.data_loader import DataLoader, Request
from code.financial_state import FinancialState, LedgerDelta
from code.forecaster import Forecaster
from code.plan_generator import PlanGenerator
from code.decision import DecisionEngine

from dotenv import load_dotenv
load_dotenv()

use_llm = "--llm" in sys.argv

llm_parser = None
if use_llm:
    try:
        from code.llm_parser import LLMParser
        llm_parser = LLMParser()
        print("LLM parser ENABLED for validation")
    except Exception as e:
        print(f"LLM init failed: {e}")

d = DataLoader("dataset/")
profiles = d.load_profiles()
sample = pd.read_csv("dataset/sample_requests.csv")

print("Comparing our engine output vs sample ground truth" + (" [LLM MODE]" if use_llm else " [DETERMINISTIC]"))
print("=" * 80)

matches = 0
mismatches = 0

for idx, (_, row) in enumerate(sample.iterrows()):
    rid = row["request_id"]
    uid = row["user_id"]
    print(f"\n[{idx+1}/25] Processing {rid}...", end=" ", flush=True)

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

    # LLM: parse messages and images for this request
    if llm_parser:
        messages = d.load_messages(rid)
        images = d.load_images(rid)
        deltas = []

        if messages:
            try:
                raw_deltas = llm_parser.parse_messages(messages)
                for dd in raw_deltas:
                    if dd.get("event_id") and dd.get("action") in ("cancel", "amend_amount", "amend_date"):
                        deltas.append(LedgerDelta(
                            event_id=dd["event_id"],
                            action=dd["action"],
                            new_value=dd.get("new_value"),
                        ))
            except Exception:
                pass

        if images:
            import os as _os
            for img in images:
                try:
                    full_path = str(os.path.join("dataset", "media", "images", f"{img.image_id}.png"))
                    if _os.path.exists(full_path):
                        result = llm_parser.extract_amount_from_image(full_path)
                        if result and img.related_event_id:
                            for e in st.events:
                                if e.event_id == img.related_event_id and e.amount is None:
                                    deltas.append(LedgerDelta(
                                        event_id=img.related_event_id,
                                        action="amend_amount",
                                        new_value=str(result["amount"]),
                                    ))
                except Exception:
                    pass

        if deltas:
            st.apply_deltas(deltas)

    fc = Forecaster(st, req)
    gn = PlanGenerator(st, req, d)
    cands = gn.generate_all_candidates()
    eng = DecisionEngine(fc)

    # LLM: rank then let AI select best candidate
    ranked = eng.rank_candidates(cands)

    if llm_parser and ranked:
        try:
            ai_choice = llm_parser.select_best_candidate(p, ranked, fc)
            if ai_choice:
                idx = ai_choice["selected_index"]
                if isinstance(idx, int) and 0 <= idx < len(ranked) and idx != 0:
                    chosen = ranked.pop(idx)
                    ranked.insert(0, chosen)
        except Exception:
            pass

    dec = eng.decide(ranked)

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

    print(f"{mark}", flush=True)

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

if llm_parser:
    usage = llm_parser.get_usage()
    print(f"LLM usage: {usage['calls']} calls, {usage['input_tokens']} in, {usage['output_tokens']} out")
