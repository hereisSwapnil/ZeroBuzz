# ZeroBuzz

> **Pure on-device notification privacy and smart semantic silence.**  
> ZeroBuzz intercepts and silences promotional noise, marketing campaigns, and clickbait notifications in real-time, while ensuring your OTPs, transactional bank alerts, food delivery updates, and personal messages always get through untouched.

---

## ✨ Features

- **🛡️ 100% On-Device Privacy**: Operates with **zero internet permissions** (`android.permission.INTERNET` is not requested). Your notification data never leaves your phone.
- **⚡ Sub-Millisecond Classification**: Custom subword n-gram semantic engine evaluates notifications in under `0.1ms` directly in native Kotlin code with 0% battery impact.
- **📱 Clean Modern UI**: Monochromatic design language inspired by modern design systems, complete with custom launcher adaptive icons and smooth interactions.
- **🎯 3-Tab Architecture**:
  1. **Whitelist**: Search and toggle any installed app to bypass filtering with zero latency. Whitelisted app notifications pass straight through and are not logged.
  2. **Activity**: Clean notification log grouped by app with instant single-tap silence/unsilence toggles (`Buzz` / `Unbuzz`).
  3. **Settings**: Master toggle for "Want buzz in your life" to pause or activate on-device filtering, plus app details.
- **🔁 Offline Sync & Continual Learning**: Connect your phone to your computer via USB to sync your custom preferences, retrain the semantic model with your feedback, and hot-update the app.

---

## ⚡ Quick Start (`just` Task Runner)

ZeroBuzz uses [`just`](https://github.com/casey/just) for one-command workflows:

| Command | Action |
| :--- | :--- |
| `just download-data` | Downloads public benchmark corpora from original sources (Hugging Face & UCI) |
| `just extract-device` | Extracts real-world notification/SMS history from connected phone into `data/device/` (git-ignored) |
| `just train` | Trains subword n-gram classifier and exports compiled Kotlin model weights |
| `just build` | Compiles the Android debug APK |
| `just install` | Installs or updates ZeroBuzz on your connected phone |
| `just sync` | Pulls feedback from phone, retrains model, and hot-updates APK in one step |

---

## 📊 Dataset & Ground-Truth Classification

### Are notifications pre-classified by an LLM?
**No LLM is used for classification.** All labels come from **deterministic ground truth**:
1. **Telecom Regulatory Suffixes (TRAI Mandate)**: Under enterprise telecom regulations, incoming sender headers are deterministically typed by the telecom network:
   - `-P` header (e.g. `AX-ZUDIO-P`, `AD-AIRTEL-P`): Promotional advertising / deals $\rightarrow$ **Label 1 (Promo Spam)**.
   - `-S` / `-T` / `-G` headers (e.g. `VM-ZAGGLE-S`, `JK-BOBOTP-T`): Service, OTP, and government alerts $\rightarrow$ **Label 0 (Allowed)**.
2. **Academic & Community Benchmarks**: Pre-annotated public datasets with human ground truth labels.
3. **Hard Mission-Critical Rules**: High-priority regex whitelisting for OTPs, transactional bank debits/credits, medications, and ride/delivery tracking guarantees **zero false positives**.

### Online Datasets & Formats

Downloaded directly from original sources via `just download-data`:

| Dataset | Source | Format & Schema | Samples |
| :--- | :--- | :--- | :--- |
| **UCI SMS Spam** | [UCI ML Repository](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) | `TSV` with columns: `label` (`ham`/`spam`), `message` | 5,574 |
| **HF Spam Messages** | [Hugging Face (`mshenoda`)](https://huggingface.co/datasets/mshenoda/spam-messages) | `CSV` with columns: `text`, `label` (`0`/`1`) | 50,000+ |
| **HF SMS OTP** | [Hugging Face (`alusci`)](https://huggingface.co/datasets/alusci/sms-otp-spam-dataset) | `CSV` with columns: `text`, `category` (`OTP`, `Auth`) | 10,000 |

All sources are unified into clean JSON structures in `data/processed/` during preprocessing:
```json
{
  "title": "Bank Alert",
  "text": "Your account has been debited by INR 250.00",
  "channel": "sms_notification",
  "label": 0
}
```

### Personal Device Data (`data/device/`)
Run `just extract-device` to extract your own phone's historical notification data via ADB. The entire `data/device/` folder is ignored by `.gitignore` to ensure your personal notifications are never committed or published.

---

## 🏗️ Project Structure

```
ZeroBuzz/
├── Justfile               # Project task runner recipes
├── android/               # Complete Android Studio project (Kotlin + Material 3)
│   ├── app/
│   │   ├── src/main/java/com/zerobuzz/
│   │   │   ├── data/      # On-device storage & state flows
│   │   │   ├── ml/        # High-speed semantic classifier & compiled weights
│   │   │   ├── service/   # NotificationListenerService implementation
│   │   │   └── ui/        # MainActivity, Adapters & view binding
│   │   └── src/main/res/  # Layouts, vector drawables & adaptive mipmap icons
│   └── build.gradle.kts
├── data/
│   ├── device/            # Local device extracted data (strictly git-ignored)
│   ├── raw/               # Download & extraction scripts
│   └── processed/         # Unified training corpora
├── ml/                    # Classifier training pipeline & model evaluation
├── scripts/               # USB device sync & retraining automated pipeline
├── .agents/               # Architecture guides, specs, and roadmaps for AI agents
├── .gitignore             # Comprehensive ignore rules
└── README.md
```

---

## 👤 Author

Developed by **[Swapnil](https://github.com/hereisswapnil)**
