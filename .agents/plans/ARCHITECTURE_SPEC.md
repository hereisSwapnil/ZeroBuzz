# ZeroBuzz: Dataset, Semantic Architecture & Engine Spec

## 1. Problem Statement
Commercial Android push notifications leverage urgency triggers, discounts, and gamification to maximize user interruptions. ZeroBuzz silences commercial spam while guaranteeing zero false positives for transactional alerts, OTPs, security notices, and delivery tracking.

---

## 2. Training Dataset Composition

The model is trained on a combined dataset comprising:
1. **Public Mobile Message Corpora**:
   - `mshenoda/spam-messages` (59,700+ rows): Short mobile messaging categorized into legitimate vs spam.
   - `alusci/sms-otp-spam-dataset` (12,000+ rows): Isolation of OTPs, financial verification codes, and alerts.
   - `Mobiusi/Promotional-Offers-And-Price-Claim` (15,000+ rows): Discount claims, flash sale alerts, promotional copy.
   - `marketeam/Marketing-Emails` (45,000+ rows): Marketing engagement triggers.
   - `UCI SMS Spam Collection` (5,574 rows): Benchmark legitimate vs commercial text.
2. **Device Corpus**:
   - Indian telecom TRAI header classifications (`-P` commercial marketing vs `-S` / `-T` transactional alerts).

---

## 3. Semantic Feature Extraction

Features are computed as linear combinations over 3 feature extractors:

1. **Word Tokens (`w:`)**:
   - Tokenized unigrams with punctuation stripping.
2. **Bigrams (`bi:`)**:
   - Word pairs capturing promotional context (e.g., `off_on`, `is_live`, `your_recharge`).
3. **Subword N-grams (`sub:`)**:
   - Character 3-grams and 4-grams capturing price points and discount triggers (e.g., `rs7`, `799`, `s348`).

### Classification Formula:
$$\text{Score} = \text{Bias} + \sum_{f \in \text{Features}} w_f$$
$$P(\text{PromoSpam}) = \sigma(\text{Score}) = \frac{1}{1 + e^{-\text{Score}}}$$

- **Threshold**: $0.50$
- **Hard Whitelist Override**: Evaluated prior to linear score; if text matches OTP or banking patterns, $P(\text{PromoSpam}) = 0.0$.
