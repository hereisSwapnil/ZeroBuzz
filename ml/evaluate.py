#!/usr/bin/env python3
"""
Benchmark & Evaluation Script for ZeroBuzz SemanticClassifier
Simulates the standalone on-device classifier using exported model_weights.json
and computes accuracy, precision, recall, F1, confusion matrix, and inference latency.
Outputs:
  - ml/eval_report.json
"""

import os
import json
import time
import math
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
WEIGHTS_PATH = os.path.join(BASE_DIR, "model_weights.json")
REPORT_PATH = os.path.join(BASE_DIR, "eval_report.json")

WHITELIST_PATTERNS = [
    re.compile(r"(?i)\b(otp|verification code|security code)\b"),
    re.compile(r"(?i)\b(dispatched|shipped|out for delivery|delivered|order\s*id|order\s*placed|placed with|tracking)\b"),
    re.compile(r"(?i)\b(credited|debited|transferred|withdrawn|paid|payment successful)\b"),
    re.compile(r"(?i)\b(driver|captain|ride started|ride completed)\b"),
    re.compile(r"(?i)\b(medication|heart rate|sleep alert|emergency)\b")
]

# Benchmark test suite representing Indian & global real-world push notification mix
BENCHMARK_SAMPLES = [
    # E-Commerce & Deliveries (Legitimate = 0)
    {"title": "Your Meesho order #8491823 has been dispatched", "text": "Your package is on its way with Shadowfax.", "channel": "orders", "expected_spam": False},
    {"title": "Order #48291 Out for delivery today", "text": "Delivery executive Ramesh will deliver your order by 7 PM.", "channel": "orders", "expected_spam": False},
    {"title": "Delivered: Printed Cotton Kurta", "text": "Your package was handed to resident at front door.", "channel": "orders", "expected_spam": False},
    
    # E-Commerce & Marketing Deals (Spam = 1)
    {"title": "Play Fest ends soon", "text": "Extra 50% discount on top games and accessories. Shop now!", "channel": "deals", "expected_spam": True},
    {"title": "Mega Blockbuster Sale is LIVE!", "text": "Grab kurtis, sarees and shirts starting at Rs 99! Shop before stock ends.", "channel": "promotions", "expected_spam": True},
    {"title": "Price dropped on items in your cart!", "text": "The Floral Dress you liked is now 40% OFF. Order now before price goes up.", "channel": "offers", "expected_spam": True},
    
    # Food & Delivery (Legitimate = 0 vs Spam = 1)
    {"title": "Delivery partner Sunil is at your door", "text": "Please collect your Swiggy order and share delivery feedback.", "channel": "live_tracking", "expected_spam": False},
    {"title": "Blinkit order delivered in 8 mins", "text": "Your 6 grocery items were safely delivered to your doorstep.", "channel": "delivery", "expected_spam": False},
    {"title": "Huge 60% discount on Pizza!", "text": "Craving cheese burst pizza? Get 50% off up to Rs 120 with code SWIGGYIT.", "channel": "offers", "expected_spam": True},
    {"title": "Craving hot snacks this afternoon?", "text": "Order hot snacks now and enjoy 40% discount with Zomato Gold.", "channel": "marketing", "expected_spam": True},
    
    # Financial & Investments (Legitimate = 0 vs Spam = 1)
    {"title": "SIP Successfully Executed", "text": "Monthly SIP of Rs 5,000 for Parag Parikh Flexi Cap Fund has been processed.", "channel": "transactions", "expected_spam": False},
    {"title": "Order Placed with AMC", "text": "Your lump sum investment order #KV8921 has been placed with Nippon India.", "channel": "transactions", "expected_spam": False},
    {"title": "Funds and stocks can overlap", "text": "Switch your regular mutual funds to direct plans in 1 tap and save up to 1.5% extra.", "channel": "promotions", "expected_spam": True},
    {"title": "Need funds on Sunday? Low interest loan ready \u2705", "text": "Instant pre-approved personal loan of Rs 5 Lakhs with zero paperwork.", "channel": "loan_offers", "expected_spam": True},
    
    # OTPs, Banking Alerts (Legitimate = 0)
    {"title": "Your OTP for HDFC Bank is 948201", "text": "948201 is your secret OTP for transaction at Amazon. Never share OTP.", "channel": "otp", "expected_spam": False},
    {"title": "Card Debited: Rs 320 at Subway", "text": "Your Zaggle Meal Card was debited for Rs 320 at Subway.", "channel": "card_alerts", "expected_spam": False},
    
    # Social, Professional & Spam (Legitimate = 0 vs Spam = 1)
    {"title": "Missed Notifications", "text": "See updates from LinkedIn that you may have missed this week.", "channel": "notifications", "expected_spam": True},
    {"title": "Ananya Sharma sent you a message", "text": "Hi Alex, I came across your profile and wanted to connect regarding an Engineering role.", "channel": "messages", "expected_spam": False},
    {"title": "People are viewing your profile", "text": "5 people viewed your profile this week. Upgrade to Premium to see who they are.", "channel": "promotions", "expected_spam": True},
    
    # Health & Medical (Legitimate = 0 vs Spam = 1)
    {"title": "Medication Reminder", "text": "Time to take Vitamin D3 (1 tablet) after lunch.", "channel": "medications", "expected_spam": False},
    {"title": "High Heart Rate Alert", "text": "Your resting heart rate exceeded 110 bpm while inactive for 10 minutes.", "channel": "heartrate", "expected_spam": False},
    {"title": "One app, your whole checkup", "text": "Book full body health checkup at 70% off with free home sample pickup.", "channel": "offers", "expected_spam": True},
    {"title": "Don't Lose Health Records Again", "text": "Digitize your medical reports and claim exclusive health insurance discounts today.", "channel": "marketing", "expected_spam": True}
]

def load_weights():
    with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation():
    model = load_weights()
    bias = model.get("bias", -9.0)
    threshold = model.get("threshold", 0.50)
    weights = model.get("features", {})

    # Warmup
    for _ in range(50):
        _ = re.sub(r'[^a-z0-9\s%]', ' ', "Warmup notification title and message text").lower().split()

    results = []
    tp = fp = tn = fn = 0
    latencies = []

    clean_regex = re.compile(r'[^a-z0-9\s%]')

    for s in BENCHMARK_SAMPLES:
        title = s["title"]
        text = s["text"]
        channel = s.get("channel", "")
        expected = s["expected_spam"]

        start_t = time.perf_counter()

        combined = f"{title} {text} {channel}"
        is_whitelisted = False
        for wp in WHITELIST_PATTERNS:
            if wp.search(combined):
                is_whitelisted = True
                break

        if is_whitelisted:
            prob = 0.0
            pred_spam = False
        else:
            clean = clean_regex.sub(' ', combined.lower())
            words = clean.split()
            score = bias

            for i in range(len(words)):
                w = words[i]
                if len(w) > 2:
                    score += weights.get(f"w:{w}", 0.0)
                if i < len(words) - 1:
                    score += weights.get(f"bi:{w}_{words[i+1]}", 0.0)
                if len(w) >= 3:
                    for length in (3, 4):
                        if len(w) >= length:
                            for st in range(len(w) - length + 1):
                                score += weights.get(f"sub:{w[st:st+length]}", 0.0)

            clamped = max(min(score, 15.0), -15.0)
            prob = 1.0 / (1.0 + math.exp(-clamped))
            pred_spam = prob >= threshold

        end_t = time.perf_counter()
        latency_us = round((end_t - start_t) * 1_000_000, 2)
        latencies.append(latency_us)

        is_correct = (pred_spam == expected)
        if expected and pred_spam:
            tp += 1
        elif not expected and not pred_spam:
            tn += 1
        elif not expected and pred_spam:
            fp += 1
        elif expected and not pred_spam:
            fn += 1

        results.append({
            "title": title,
            "prob": round(prob, 2),
            "predicted_spam": pred_spam,
            "expected_spam": expected,
            "correct": is_correct,
            "latency_us": latency_us
        })

    total = len(BENCHMARK_SAMPLES)
    acc = round(((tp + tn) / total) * 100.0, 2)
    prec = round((tp / (tp + fp)) * 100.0, 2) if (tp + fp) > 0 else 0.0
    rec = round((tp / (tp + fn)) * 100.0, 2) if (tp + fn) > 0 else 0.0
    f1 = round((2 * prec * rec / (prec + rec)), 2) if (prec + rec) > 0 else 0.0
    avg_latency = round(sum(latencies) / len(latencies), 1)

    eval_data = {
        "metrics": {
            "total_test_samples": total,
            "accuracy_percent": acc,
            "precision_percent": prec,
            "recall_percent": rec,
            "f1_score": f1,
            "avg_latency_microseconds": avg_latency,
            "avg_latency_milliseconds": round(avg_latency / 1000.0, 4)
        },
        "confusion_matrix": {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn
        },
        "sample_evaluations": results
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)

    print(f"✅ Evaluation complete:")
    print(f"   Accuracy:  {acc}%")
    print(f"   Precision: {prec}%")
    print(f"   Recall:    {rec}%")
    print(f"   F1-Score:  {f1}%")
    print(f"   Avg Latency: {avg_latency} µs ({avg_latency/1000.0:.4f} ms)")
    print(f"   Saved report to: {REPORT_PATH}")

if __name__ == "__main__":
    run_evaluation()
