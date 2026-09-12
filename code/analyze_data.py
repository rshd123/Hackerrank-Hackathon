"""Analyze user_01 and user_02 financial state deeply"""
import csv
from collections import defaultdict

def load_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

events = load_csv('dataset/financial_events.csv')
profiles = {r['user_id']: r for r in load_csv('dataset/financial_profiles.csv')}
options = load_csv('dataset/request_payment_options.csv')
messages = load_csv('dataset/messages.csv')

# === USER_01 ===
print("=" * 60)
print("USER_01 PROFILE")
print("=" * 60)
p1 = profiles['user_01']
for k, v in p1.items():
    print(f"  {k}: {v}")

user1_events = [e for e in events if e['user_id'] == 'user_01']
print(f"\nTotal events: {len(user1_events)}")

# Recurring expenses
settled_debits = [e for e in user1_events if e['status'] == 'settled' and e['direction'] == 'debit']
cats = defaultdict(list)
for e in settled_debits:
    cats[e['category']].append(e)

print("\nRecurring expense categories:")
for cat, evts in sorted(cats.items()):
    amounts = [float(e['amount'].replace(',', '')) for e in evts if e.get('amount')]
    if amounts:
        print(f"  {cat}: {len(evts)} events, amounts: {amounts[:3]}... avg={sum(amounts)/len(amounts):.2f}")

# Income/credits
credits = [e for e in user1_events if e['direction'] == 'credit']
print(f"\nCredit events: {len(credits)}")
for c in credits[:5]:
    print(f"  {c['event_date']} | {c['description']} | {c['amount']} | {c['status']}")

# Pending events
pending = [e for e in user1_events if e['status'] == 'pending']
print(f"\nPending events: {len(pending)}")
for p in pending:
    print(f"  {p['event_date']} | {p['description']} | {p['amount']} | {p['direction']}")

# Flexible events
flexible = [e for e in user1_events if e.get('flexibility') in ('stoppable', 'reducible')]
print(f"\nFlexible events: {len(flexible)}")
for f in flexible[:10]:
    print(f"  {f['event_id']} | {f['category']} | {f['amount']} | {f['flexibility']}")

# Payment options for request_01
print("\nPayment options for request_01:")
req01_opts = [o for o in options if o['request_id'] == 'request_01']
for o in req01_opts:
    print(f"  {o['payment_option_id']} | {o['payment_method']} | amount={o['payment_amount']} | "
          f"n={o['number_of_payments']} | fee={o['financing_fee']} | total={o['total_payable_amount']}")

# Messages for user_01
user1_msgs = [m for m in messages if m['user_id'] == 'user_01']
print(f"\nMessages for user_01: {len(user1_msgs)}")
for m in user1_msgs:
    print(f"  {m['sent_at']} | {m['source_type']} | {m['message_text'][:80]}...")

# === USER_02 ===
print("\n" + "=" * 60)
print("USER_02 PROFILE")
print("=" * 60)
p2 = profiles['user_02']
for k, v in p2.items():
    print(f"  {k}: {v}")

user2_events = [e for e in events if e['user_id'] == 'user_02']
print(f"\nTotal events: {len(user2_events)}")

# Income
credits2 = [e for e in user2_events if e['direction'] == 'credit']
print(f"Credit events: {len(credits2)}")
for c in credits2[:5]:
    print(f"  {c['event_date']} | {c['description']} | {c['amount']} | {c['status']}")

# Messages for user_02
user2_msgs = [m for m in messages if m['user_id'] == 'user_02']
print(f"\nMessages for user_02: {len(user2_msgs)}")
for m in user2_msgs:
    print(f"  {m['sent_at']} | {m['source_type']} | {m['message_text'][:100]}")

# Payment options for request_02
print("\nPayment options for request_02:")
req02_opts = [o for o in options if o['request_id'] == 'request_02']
for o in req02_opts:
    print(f"  {o['payment_option_id']} | {o['payment_method']} | amount={o['payment_amount']} | "
          f"n={o['number_of_payments']} | fee={o['financing_fee']} | total={o['total_payable_amount']}")

# === REQUEST_19 (partial payment example) ===
print("\n" + "=" * 60)
print("REQUEST_19 (partial_payment example)")
print("=" * 60)
p19 = profiles['user_19']
print(f"Balance: {p19['current_available_balance']}")
print(f"Min: {p19['minimum_balance_to_keep']}")
print(f"Prefs: {p19['payment_methods_user_will_consider']}")
req19_opts = [o for o in options if o['request_id'] == 'request_19']
for o in req19_opts:
    print(f"  {o['payment_option_id']} | {o['payment_method']} | amount={o['payment_amount']} | "
          f"n={o['number_of_payments']} | total={o['total_payable_amount']}")

# === REQUEST_06 (spending changes example) ===
print("\n" + "=" * 60)
print("REQUEST_06 (spending_changes example)")
print("=" * 60)
p6 = profiles['user_06']
print(f"Balance: {p6['current_available_balance']}")
print(f"Min: {p6['minimum_balance_to_keep']}")
print(f"Prefs: {p6['payment_methods_user_will_consider']}")
user6_events = [e for e in events if e['user_id'] == 'user_06']
flexible6 = [e for e in user6_events if e.get('flexibility') in ('stoppable', 'reducible')]
print(f"Flexible events: {len(flexible6)}")
for f in flexible6:
    print(f"  {f['event_id']} | {f['category']} | {f['amount']} | {f['flexibility']}")
