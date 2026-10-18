# ZeroBuzz Project Justfile

default:
    @just --list

# End-to-end dataset pipeline: download online corpora, extract device notifications, and train model
pretrain:
    @echo "==> Step 1/3: Downloading online corpora..."
    just download-data
    @echo "\n==> Step 2/3: Extracting device history..."
    -just extract-device
    @echo "\n==> Step 3/3: Merging datasets and training classifier..."
    just train

# Download public benchmark notification & message corpora from original sources (Hugging Face & UCI)
download-data:
    python3 data/raw/download_online_corpora.py

# Extract real-world notification and message history from connected Android device via ADB
extract-device:
    python3 data/raw/extract_device_history.py

# Train the semantic subword model and export compiled Kotlin classifier weights
train:
    python3 ml/train.py

# Compile the ZeroBuzz Android application (Debug APK)
build:
    cd android && ./gradlew assembleDebug

# Install ZeroBuzz onto connected Android phone (Primary default user only)
install:
    adb install --user 0 -r android/app/build/outputs/apk/debug/app-debug.apk

# Clean build caches and temporary gradle artifacts
clean:
    cd android && ./gradlew clean
    rm -rf android/app/build android/.gradle

# Pull preference feedback from phone, save to data/device, and clear phone cache
sync:
    python3 scripts/sync_and_retrain.py

# Optional all-in-one: sync feedback, retrain, compile, and hot-install on phone
sync-all:
    python3 scripts/sync_and_retrain.py --all

# Stage a versioned APK in releases/ folder (e.g. `just stage-release v1.0.0`)
stage-release VERSION="v1.0.0":
    @echo "📦 Building ZeroBuzz APK for {{VERSION}}..."
    cd android && ./gradlew assembleDebug
    @mkdir -p releases
    cp android/app/build/outputs/apk/debug/app-debug.apk releases/ZeroBuzz-{{VERSION}}.apk
    @echo "✅ Prepared release binary: releases/ZeroBuzz-{{VERSION}}.apk"
    @echo "💡 When ready to publish to GitHub, run: just publish-release {{VERSION}}"

# Publish release and APK to GitHub as an attached download (DO NOT run until ready to release)
publish-release VERSION="v1.0.0":
    @if [ ! -f "releases/ZeroBuzz-{{VERSION}}.apk" ]; then \
        echo "❌ Release binary not found. Running stage-release first..."; \
        just stage-release {{VERSION}}; \
    fi
    gh release create {{VERSION}} releases/ZeroBuzz-{{VERSION}}.apk \
        --title "ZeroBuzz {{VERSION}}" \
        --notes-file releases/RELEASE_NOTES.md
