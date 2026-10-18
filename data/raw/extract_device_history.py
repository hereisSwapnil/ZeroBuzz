#!/usr/bin/env python3
"""
Device Notification & History Extractor for ZeroBuzz
Extracts real-world notification and message records from any connected Android phone via ADB:
1. Android Dumpsys (active notifications currently on the device)
2. Device Incoming Telephony/SMS Provider (with TRAI regulatory header classifications)

Outputs directly to data/device/device_extracted_history.json (ignored by Git for privacy).
"""

import os
import sys
import subprocess
import json
import re
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DEVICE_DATA_DIR = os.path.join(PROJECT_DIR, "data", "device")
os.makedirs(DEVICE_DATA_DIR, exist_ok=True)
OUT_PATH = os.path.join(DEVICE_DATA_DIR, "device_extracted_history.json")

SAMPLE_FIRST_NAMES = ['Ramesh', 'Priya', 'Amit', 'Rohit', 'Neha', 'Vikas', 'Pooja', 'Sunil', 'Kavita', 'Suresh', 'Aman', 'Ananya', 'Rahul', 'Deepak', 'Arjun', 'Sneha']
SAMPLE_DOMAINS = ['gmail.com', 'outlook.com', 'yahoo.com', 'icloud.com', 'proton.me']
SAMPLE_VPA_BANKS = ['okhdfcbank', 'okaxis', 'okicici', 'ybl', 'paytm', 'ibl', 'axl', 'yesfam']

def anonymize_text(text):
    if not text:
        return text

    # 1. User specific names, handles, usernames
    text = re.sub(r'(?i)[a-z0-9_\.]*swapnil[a-z0-9_\.]*',
                  lambda _: random.choice(SAMPLE_FIRST_NAMES).lower() + str(random.randint(10, 99)), text)

    # 2. UPI VPA addresses
    def rand_vpa(_):
        u = random.choice(SAMPLE_FIRST_NAMES).lower() + str(random.randint(10, 999))
        return f'{u}@{random.choice(SAMPLE_VPA_BANKS)}'
    text = re.sub(r'[a-zA-Z0-9_\.\-]+@(yesfam|okhdfcbank|okicici|okaxis|ybl|paytm|apl|ibl|axl|upi)', rand_vpa, text)

    # 3. Standard email addresses
    def rand_email(_):
        u = random.choice(SAMPLE_FIRST_NAMES).lower() + str(random.randint(10, 999))
        return f'{u}@{random.choice(SAMPLE_DOMAINS)}'
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', rand_email, text)

    # 4. Greeting name patterns (Dear Priya, Hi Amit, etc.)
    text = re.sub(r'(?i)\b(dear|hi|hello|hey|mr\.|mrs\.|ms\.)\s+([a-z]+)\b',
                  lambda m: f'{m.group(1)} {random.choice(SAMPLE_FIRST_NAMES)}', text)

    # 5. Indian Phone numbers (10 digits)
    def rand_phone(_):
        pfx = random.choice(['98', '97', '99', '88', '89', '70', '79', '91', '94'])
        body = ''.join(str(random.randint(0, 9)) for _ in range(8))
        return f'{pfx}{body}'
    text = re.sub(r'(?:\+?91[\-\s]?)?[6-9]\d{9}', rand_phone, text)

    # 6. Bank Account & Card masks
    def rand_masked_acct(m):
        prefix = m.group(1)
        return f'{prefix}{random.randint(1000, 9999)}'
    text = re.sub(r'(?i)(a/c\s*(?:no\.?|ending|is)?\s*[:\*\sxX]*)\b\d{4,}\b', rand_masked_acct, text)
    text = re.sub(r'(?i)(card\s*(?:no\.?|ending|is)?\s*[:\*\sxX]*)\b\d{4,}\b', rand_masked_acct, text)
    text = re.sub(r'(?i)([x\*]{2,}\s*)\d{4,}\b', rand_masked_acct, text)

    # 7. Any remaining 4-16 digit numbers (OTPs, PNRs, reference numbers)
    def rand_digits(m):
        s = m.group(0)
        if s in ['2020', '2021', '2022', '2023', '2024', '2025', '2026', '2027']:
            return s
        return ''.join(str(random.randint(0, 9)) for _ in range(len(s)))
    text = re.sub(r'\d{4,16}', rand_digits, text)

    return text

def get_connected_device():
    res = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("❌ Error executing adb. Ensure Android platform-tools are in your PATH.")
        sys.exit(1)
        
    devices = []
    for line in res.stdout.splitlines()[1:]:
        parts = line.strip().split("\t")
        if len(parts) == 2 and parts[1] == "device":
            devices.append(parts[0])
            
    if not devices:
        print("❌ No Android device found. Connect your phone via USB with USB Debugging enabled.")
        sys.exit(1)
        
    device = devices[0]
    print(f"📱 Connected Device: {device}")
    return device

def extract_from_device():
    print("=" * 60)
    print("EXTRACTING NOTIFICATION & MESSAGE HISTORY FROM DEVICE")
    print("=" * 60)
    
    device = get_connected_device()
    extracted_records = []
    seen_texts = set()

    # 1. Query Active Notifications via Dumpsys
    print("🔍 Querying active notifications via dumpsys...")
    dumpsys_cmd = ["adb", "-s", device, "shell", "dumpsys", "notification", "--noredact"]
    res_dump = subprocess.run(dumpsys_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    
    # Parse notification records from dumpsys
    # Look for NotificationRecord patterns
    lines = res_dump.stdout.splitlines()
    cur_pkg = None
    cur_title = ""
    cur_text = ""
    
    for line in lines:
        line_s = line.strip()
        if "NotificationRecord(" in line_s and "pkg=" in line_s:
            pkg_m = re.search(r"pkg=([a-zA-Z0-9_\.]+)", line_s)
            if pkg_m:
                cur_pkg = pkg_m.group(1)
        if "tickerText=" in line_s and cur_pkg:
            txt_m = re.search(r"tickerText=(.*)", line_s)
            if txt_m and txt_m.group(1) != "null":
                cur_text = txt_m.group(1).strip()
        if "android.title=" in line_s:
            title_m = re.search(r"android\.title=String \((.*?)\)", line_s)
            if title_m:
                cur_title = title_m.group(1).strip()
        if "android.text=" in line_s and cur_pkg and cur_title:
            text_m = re.search(r"android\.text=String \((.*?)\)", line_s)
            if text_m:
                cur_text = text_m.group(1).strip()
                
            combined = f"{cur_title} {cur_text}".lower().strip()
            if len(combined) > 5 and combined not in seen_texts:
                seen_texts.add(combined)
                # Quick heuristic for active notifications
                is_promo = any(w in combined for w in ["sale", "off", "deal", "discount", "loan", "free", "hurry"])
                anon_title = anonymize_text(cur_title)
                anon_text = anonymize_text(cur_text)
                extracted_records.append({
                    "pkg": cur_pkg,
                    "app": cur_pkg.split(".")[-1].capitalize(),
                    "channel": "active_dumpsys",
                    "importance": 3,
                    "title": anon_title,
                    "text": anon_text,
                    "label": 1 if is_promo else 0,
                    "category": "ACTIVE_PUSH_NOTIFICATION"
                })
            cur_pkg = None
            cur_title = ""
            cur_text = ""

    print(f"Retrieved {len(extracted_records)} active notifications from dumpsys.")

    # 2. Query Incoming Telephony/SMS Provider
    print("🔍 Querying device telephony message provider...")
    sms_cmd = [
        "adb", "-s", device, "shell",
        'content query --uri content://sms --projection body:address:type:date --where "type=1"'
    ]
    res_sms = subprocess.run(sms_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    raw_lines = res_sms.stdout.splitlines()
    print(f"Retrieved {len(raw_lines)} incoming entries from device.")

    promo_count = 0
    essential_count = 0

    for line in raw_lines:
        m = re.search(r"body=(.*?),\s*address=([A-Za-z0-9_\-+]+),\s*type=1", line)
        if not m:
            continue
        body = m.group(1).strip()
        addr = m.group(2).strip()

        # Noise / Token filter
        if len(body) < 15 or body.startswith("YESPRODUPI") or body.startswith("GET_TOKEN"):
            continue

        clean_key = body.lower().strip()
        if clean_key in seen_texts:
            continue
        seen_texts.add(clean_key)

        # Regulatory Classification (TRAI standards)
        # -P suffix = Strictly Promotional (commercial marketing)
        # -S suffix = Service updates (bank alerts, card debits, tracking)
        # -T suffix = Transactional (OTPs, two-factor authentication)
        # -G suffix = Government alerts
        is_promo = False
        cat = "TRANSACTIONAL"

        if addr.endswith("-P") or "-P-" in addr:
            is_promo = True
            cat = "COMMERCIAL_MARKETING_PROMO"
        elif any(k in addr.upper() for k in ["RWD", "DEAL", "OFFER", "SALE", "PROMO"]):
            is_promo = True
            cat = "DISCOUNT_PROMO"
        else:
            has_promo_terms = any(w in body.lower() for w in [
                "hurry", "flat off", "% off", "discount code", "coupon code", "win up to",
                "limited time offer", "cashback up to", "exclusive deal", "free delivery",
                "buy 1 get 1", "sale is live", "pre-approved loan", "lowest emi", "instant loan"
            ])
            has_essential_terms = any(w in body.lower() for w in [
                "otp", "debited", "credited", "balance", "spent", "sent to your",
                "alert:", "firing", "incident", "assigned to you", "blocked", "account", "valid till"
            ])

            if has_promo_terms and not has_essential_terms:
                is_promo = True
                cat = "IN_APP_MARKETING_PROMO"
            elif has_essential_terms:
                is_promo = False
                cat = "BANKING_SECURITY_OR_OTP"
            else:
                if addr.endswith("-S") or addr.endswith("-T") or addr.endswith("-G"):
                    is_promo = False
                    cat = "SERVICE_COMMUNICATION"
                else:
                    is_promo = False
                    cat = "GENERAL_NOTIFICATION"

        label = 1 if is_promo else 0
        if label == 1:
            promo_count += 1
        else:
            essential_count += 1

        title = addr
        text_content = body
        if ":" in body[:30]:
            parts = body.split(":", 1)
            if len(parts[0]) < 25:
                title = f"{addr}: {parts[0].strip()}"
                text_content = parts[1].strip()

        anon_title = anonymize_text(title)
        anon_text = anonymize_text(text_content)

        extracted_records.append({
            "pkg": "com.android.mms",
            "app": addr,
            "channel": "sms_notification",
            "importance": 3 if label == 0 else 2,
            "title": anon_title,
            "text": anon_text,
            "label": label,
            "category": cat
        })

    print(f"Total Unique Device Records: {len(extracted_records)}")
    print(f"  - Promotional (Label 1): {promo_count}")
    print(f"  - Essential (Label 0):   {essential_count}")

    data_payload = {
        "extracted_at": datetime.now().isoformat(),
        "total_records": len(extracted_records),
        "notes": "Extracted from connected device via dumpsys and telephony provider with TRAI regulatory verification.",
        "records": extracted_records
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2, ensure_ascii=False)
    print(f"✅ Successfully saved to: {OUT_PATH}")

if __name__ == "__main__":
    extract_from_device()
