#!/usr/bin/env python3
"""
Downloads the public online notification and mobile message datasets:
1. UCI SMS Spam Collection (5,574 samples)
2. Hugging Face mshenoda/spam-messages (50,000+ samples)
3. Hugging Face alusci/sms-otp-spam-dataset (10,000 OTP & authentication samples)
"""

import os
import urllib.request
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "online_corpora")
os.makedirs(OUT_DIR, exist_ok=True)

DATASETS = [
    {
        "name": "UCI SMS Spam Collection",
        "file": os.path.join(OUT_DIR, "uci_sms_spam.tsv"),
        "url": "https://raw.githubusercontent.com/justmarkham/DAT8/master/data/sms.tsv"
    },
    {
        "name": "Hugging Face mshenoda/spam-messages",
        "file": os.path.join(OUT_DIR, "hf_spam_messages.csv"),
        "url": "https://huggingface.co/datasets/mshenoda/spam-messages/resolve/main/spam_messages_train.csv"
    },
    {
        "name": "Hugging Face alusci/sms-otp-spam-dataset",
        "file": os.path.join(OUT_DIR, "hf_sms_otp.csv"),
        "url": "https://huggingface.co/datasets/alusci/sms-otp-spam-dataset/resolve/main/SMS_OTP_10000_samples.csv"
    }
]

def download_corpora():
    print("=" * 60)
    print("DOWNLOADING ONLINE NOTIFICATION & MESSAGE CORPORA")
    print("=" * 60)
    for d in DATASETS:
        dest = d["file"]
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f"Already downloaded: {d['name']} ({os.path.getsize(dest) / 1024:.1f} KB)")
            continue
        print(f"Downloading {d['name']} from {d['url']}...")
        try:
            req = urllib.request.Request(d["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out_f:
                out_f.write(resp.read())
            print(f"Saved to: {dest} ({os.path.getsize(dest) / 1024:.1f} KB)")
        except Exception as e:
            print(f"Failed to download {d['name']}: {e}")

if __name__ == "__main__":
    download_corpora()
