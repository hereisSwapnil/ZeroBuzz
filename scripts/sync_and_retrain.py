#!/usr/bin/env python3
"""
ZeroBuzz Laptop Sync & Retraining Pipeline
Run this single command whenever your phone is connected via USB:
  python3 scripts/sync_and_retrain.py

Workflow:
1. Pulls user label corrections (changed notification preferences) from your phone.
2. Ingests your corrected preferences into the 15,000+ sample training dataset.
3. Retrains the semantic model with updated weights.
4. Compiles and hot-updates the ZeroBuzz APK on your phone in place (-r).
"""

import os
import sys
import subprocess
import json

from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_DIR)

try:
    from ml.train import anonymize_text
except ImportError:
    def anonymize_text(t):
        return t

DATA_DIR = os.path.join(PROJECT_DIR, "data")
DEVICE_DIR = os.path.join(DATA_DIR, "device")
os.makedirs(DEVICE_DIR, exist_ok=True)
PROCESSED_FILE = os.path.join(DATA_DIR, "processed", "combined_notification_dataset.json")

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ Error executing: {cmd}")
        print(res.stderr.strip())
        return None
    return res.stdout.strip()

def check_device():
    out = run("adb devices")
    lines = [l for l in out.splitlines() if "\tdevice" in l]
    if not lines:
        print("❌ No Android device found. Make sure USB Debugging is enabled.")
        sys.exit(1)
    device_id = lines[0].split("\t")[0]
    print(f"📱 Connected Device: {device_id}")
    return device_id

def clear_mobile_feedback(device_id):
    """Clears user_corrections.json files on phone so subsequent syncs don't bring duplicates."""
    remote_paths = [
        "/sdcard/Android/data/com.zerobuzz/files/user_corrections.json",
        "/sdcard/Download/zerobuzz_corrections.json"
    ]
    for p in remote_paths:
        run(f"adb -s {device_id} shell rm -f {p}")
    # Also clear internal files via run-as
    run(f"adb -s {device_id} shell 'run-as com.zerobuzz rm -f files/user_corrections.json 2>/dev/null || true'")
    print(f"🧹 Cleared mobile feedback files on {device_id} to prevent duplicate syncs.")

def pull_corrections(device_id):
    print("📥 Checking for user preference corrections on phone...")
    corrections_data = None
    tmp_local = os.path.join(DEVICE_DIR, "tmp_pull.json")

    # Method 1: Check app external files directory
    remote_path = "/sdcard/Android/data/com.zerobuzz/files/user_corrections.json"
    exists = run(f"adb -s {device_id} shell '[ -f {remote_path} ] && echo EXISTS || true'")
    if exists == "EXISTS":
        run(f"adb -s {device_id} pull {remote_path} {tmp_local}")
        if os.path.exists(tmp_local):
            try:
                with open(tmp_local) as f:
                    corrections_data = json.load(f)
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_local):
                    os.remove(tmp_local)

    # Method 2: Check public downloads folder
    if not corrections_data:
        dl_path = "/sdcard/Download/zerobuzz_corrections.json"
        exists_dl = run(f"adb -s {device_id} shell '[ -f {dl_path} ] && echo EXISTS || true'")
        if exists_dl == "EXISTS":
            run(f"adb -s {device_id} pull {dl_path} {tmp_local}")
            if os.path.exists(tmp_local):
                try:
                    with open(tmp_local) as f:
                        corrections_data = json.load(f)
                except Exception:
                    pass
                finally:
                    if os.path.exists(tmp_local):
                        os.remove(tmp_local)

    # Method 3: Try run-as
    if not corrections_data:
        raw = run(f"adb -s {device_id} exec-out run-as com.zerobuzz cat files/user_corrections.json")
        if raw and raw.startswith("["):
            try:
                corrections_data = json.loads(raw)
            except Exception:
                pass

    if not corrections_data:
        print("ℹ️ No new user preference changes found on phone. (Using existing dataset)")
        return []

    print(f"✅ Found {len(corrections_data)} user preference changes on phone!")
    sanitized_corrections = []
    for idx, c in enumerate(corrections_data):
        c["title"] = anonymize_text(c.get("title", ""))
        c["text"] = anonymize_text(c.get("text", ""))
        label_str = "BLOCKED (Spam)" if c["corrected_label"] == 1 else "ALLOWED (Legitimate)"
        print(f"   [{idx+1}] '{c['title']}': marked as {label_str}")
        sanitized_corrections.append(c)

    # Save under data/device with timestamp naming
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    feedback_file = os.path.join(DEVICE_DIR, f"feedback_{ts}.json")
    with open(feedback_file, "w", encoding="utf-8") as f:
        json.dump(sanitized_corrections, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(sanitized_corrections)} corrections to: {feedback_file}")

    # Clear feedback from mobile so next sync doesn't re-import duplicates
    clear_mobile_feedback(device_id)

    return sanitized_corrections

def merge_and_retrain(corrections):
    print("\n🧠 Retraining semantic classifier on updated dataset (ingesting all data/device files)...")
    train_script = os.path.join(PROJECT_DIR, "ml", "train.py")
    train_out = run(f"python3 {train_script}", cwd=PROJECT_DIR)
    if train_out:
        print("✅ Model weights updated and SemanticClassifier.kt re-generated.")

def build_and_update(device_id):
    print("\n🔨 Building updated ZeroBuzz APK...")
    android_dir = os.path.join(PROJECT_DIR, "android")
    build_out = run("./gradlew assembleDebug", cwd=android_dir)
    if build_out is None:
        print("❌ Build failed.")
        sys.exit(1)

    apk_path = os.path.join(android_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if not os.path.exists(apk_path):
        print(f"❌ APK not found at: {apk_path}")
        sys.exit(1)

    print("🚀 Hot-updating ZeroBuzz on your phone (-r preserves your settings)...")
    install_out = run(f"adb -s {device_id} install --user 0 -r {apk_path}")
    print(f"📲 {install_out}")
    print("\n✨ Sync & Retraining Complete! Your phone is running the updated model.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ZeroBuzz Feedback Sync & Retraining Pipeline")
    parser.add_argument("--all", action="store_true", help="Pull feedback, retrain model, compile APK, and hot-install on phone")
    args = parser.parse_args()

    print("=" * 60)
    print("⚡ ZEROBUZZ MOBILE FEEDBACK SYNC")
    print("=" * 60)
    dev = check_device()
    corrections = pull_corrections(dev)

    if args.all:
        merge_and_retrain(corrections)
        build_and_update(dev)
    else:
        print("\n✨ Sync complete! Preference changes are saved in data/device/.")
        print("💡 Next steps:")
        print("   - Run 'just train'   to retrain model weights")
        print("   - Run 'just build'   to compile the APK")
        print("   - Run 'just install' to update on phone")

