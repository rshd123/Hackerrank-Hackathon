import sys
sys.path.insert(0, ".")
import pandas as pd
from code.data_loader import DataLoader

d = DataLoader("dataset/")
sample = pd.read_csv("dataset/sample_requests.csv")

total_msgs = 0
total_imgs = 0
for _, row in sample.iterrows():
    rid = row["request_id"]
    msgs = d.load_messages(rid)
    imgs = d.load_images(rid)
    total_msgs += len(msgs)
    total_imgs += len(imgs)
    if msgs or imgs:
        print(f"{rid}: {len(msgs)} msgs, {len(imgs)} imgs")

print(f"\nTotal: {total_msgs} msgs, {total_imgs} imgs")
print(f"Estimated LLM calls: {total_msgs} message parses + {total_imgs} image OCRs + 25 candidate selects = ~{total_msgs + total_imgs + 25} calls")
print(f"Estimated time: {(total_msgs + total_imgs + 25) * 2.1 / 60:.1f} minutes (at 2.1s/call)")
