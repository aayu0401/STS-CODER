"""
STS Coder — Model Training Pipeline
======================================
Trains two scikit-learn classifiers:
  1. Entry Type Classifier  (RandomForest)
  2. Risk Level Classifier  (RandomForest)

Uses regex-based feature extraction from TPF assembly text.
Models are serialized to disk via joblib for API inference.

Usage:
  python -m training.train_model
"""

import re
import os
import json
import numpy as np
from datetime import datetime, timezone

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib

from training.training_data import (
    TRAINING_SAMPLES,
    FEATURE_PATTERNS,
    ENTRY_TYPES,
    RISK_LEVELS,
)


# ═══════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════

MODEL_DIR = os.path.join(os.path.dirname(__file__), "data")
TYPE_MODEL_PATH = os.path.join(MODEL_DIR, "entry_type_model.joblib")
RISK_MODEL_PATH = os.path.join(MODEL_DIR, "risk_level_model.joblib")
TYPE_ENCODER_PATH = os.path.join(MODEL_DIR, "type_encoder.joblib")
RISK_ENCODER_PATH = os.path.join(MODEL_DIR, "risk_encoder.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


# ═══════════════════════════════════════════
# FEATURE EXTRACTION
# ═══════════════════════════════════════════

COMPILED_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for name, pattern in FEATURE_PATTERNS.items()
}


def extract_features(text: str) -> np.ndarray:
    """
    Extract binary + count features from raw TPF assembly text.
    Returns a 1D numpy array of shape (num_features,).
    """
    features = []

    # Binary pattern features (0 or 1)
    for name, pattern in COMPILED_PATTERNS.items():
        features.append(1.0 if pattern.search(text) else 0.0)

    # Count features
    features.append(float(len(re.findall(r"\bDS\b|\bDC\b", text, re.IGNORECASE))))  # var_count
    features.append(float(len(re.findall(r"\bB\s+\w|BE\s+|BNE\s+|BH\s+|BL\s+", text, re.IGNORECASE))))  # branch_count
    features.append(float(len(re.findall(r"\bMVC\b|\bMVI\b|\bL\s+|LA\s+|ST\s+", text, re.IGNORECASE))))  # data_ops
    features.append(float(text.count("\n")))  # line_count
    features.append(float(len(re.findall(r"^\w+\s+CSECT|^\w+\s+DS\s+0H", text, re.IGNORECASE | re.MULTILINE))))  # label_count

    return np.array(features, dtype=np.float64)


def get_feature_names() -> list[str]:
    """Return ordered feature names for interpretability."""
    names = list(FEATURE_PATTERNS.keys())
    names.extend(["var_count", "branch_count", "data_ops", "line_count", "label_count"])
    return names


# ═══════════════════════════════════════════
# DATA AUGMENTATION
# ═══════════════════════════════════════════

def augment_samples(samples: list[dict], factor: int = 5) -> list[dict]:
    """
    Augment training data by creating variations:
    - Whitespace changes
    - Comment insertion
    - Label renaming
    - Instruction reordering (safe)
    """
    augmented = list(samples)  # keep originals

    for _ in range(factor):
        for sample in samples:
            text = sample["entry_text"]
            lines = text.strip().split("\n")

            # Variation 1: Add random comments
            insert_idx = min(2, len(lines))
            lines.insert(insert_idx, f"* COMMENT LINE {np.random.randint(1000, 9999)}")

            # Variation 2: Vary whitespace
            varied = []
            for line in lines:
                if line.startswith("*"):
                    varied.append(line)
                else:
                    spaces = " " * np.random.randint(7, 12)
                    parts = line.split(None, 1)
                    if len(parts) == 2 and not line[0].isspace():
                        varied.append(f"{parts[0]}{spaces}{parts[1]}")
                    else:
                        varied.append(line)

            new_text = "\n".join(varied)
            augmented.append({
                **sample,
                "entry_text": new_text,
            })

    return augmented


# ═══════════════════════════════════════════
# TRAINING
# ═══════════════════════════════════════════

def train():
    """
    Train both classifiers and save to disk.
    Returns training metrics dict.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("=" * 60)
    print("  STS Coder — Model Training Pipeline")
    print("=" * 60)

    # Augment data
    print(f"\n[1/5] Augmenting training data...")
    augmented = augment_samples(TRAINING_SAMPLES, factor=8)
    print(f"  Original samples: {len(TRAINING_SAMPLES)}")
    print(f"  Augmented samples: {len(augmented)}")

    # Extract features
    print(f"\n[2/5] Extracting features...")
    X = np.array([extract_features(s["entry_text"]) for s in augmented])
    y_type = [s["entry_type"] for s in augmented]
    y_risk = [s["risk_level"] for s in augmented]
    print(f"  Feature vector size: {X.shape[1]}")
    print(f"  Feature names: {get_feature_names()}")

    # Encode labels
    type_encoder = LabelEncoder()
    risk_encoder = LabelEncoder()
    y_type_enc = type_encoder.fit_transform(y_type)
    y_risk_enc = risk_encoder.fit_transform(y_risk)

    # Train Entry Type Classifier
    print(f"\n[3/5] Training Entry Type Classifier...")
    type_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )
    type_model.fit(X, y_type_enc)

    # Cross-validate
    n_splits = min(3, len(set(y_type_enc)))
    if n_splits >= 2:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        type_scores = cross_val_score(type_model, X, y_type_enc, cv=cv, scoring="accuracy")
        print(f"  Cross-val accuracy: {type_scores.mean():.4f} (+/- {type_scores.std():.4f})")
    else:
        type_scores = np.array([1.0])
        print(f"  (Too few classes for cross-validation)")

    # Train Risk Level Classifier
    print(f"\n[4/5] Training Risk Level Classifier...")
    risk_model = GradientBoostingClassifier(
        n_estimators=80,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
    )
    risk_model.fit(X, y_risk_enc)

    n_risk_splits = min(3, len(set(y_risk_enc)))
    if n_risk_splits >= 2:
        cv_risk = StratifiedKFold(n_splits=n_risk_splits, shuffle=True, random_state=42)
        risk_scores = cross_val_score(risk_model, X, y_risk_enc, cv=cv_risk, scoring="accuracy")
        print(f"  Cross-val accuracy: {risk_scores.mean():.4f} (+/- {risk_scores.std():.4f})")
    else:
        risk_scores = np.array([1.0])

    # Save models
    print(f"\n[5/5] Saving models...")
    joblib.dump(type_model, TYPE_MODEL_PATH)
    joblib.dump(risk_model, RISK_MODEL_PATH)
    joblib.dump(type_encoder, TYPE_ENCODER_PATH)
    joblib.dump(risk_encoder, RISK_ENCODER_PATH)
    print(f"  Saved: {TYPE_MODEL_PATH}")
    print(f"  Saved: {RISK_MODEL_PATH}")

    # Feature importance
    feature_names = get_feature_names()
    importances = type_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    print(f"\n  Top Feature Importances (Type Classifier):")
    for i in range(min(8, len(feature_names))):
        idx = sorted_idx[i]
        print(f"    {feature_names[idx]:24s} {importances[idx]:.4f}")

    # Save metadata
    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(TRAINING_SAMPLES),
        "augmented_samples": len(augmented),
        "feature_count": X.shape[1],
        "feature_names": feature_names,
        "entry_types": list(type_encoder.classes_),
        "risk_levels": list(risk_encoder.classes_),
        "type_cv_accuracy": float(type_scores.mean()),
        "risk_cv_accuracy": float(risk_scores.mean()),
        "type_feature_importances": {
            feature_names[i]: float(importances[i]) for i in sorted_idx[:10]
        },
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Saved: {METADATA_PATH}")

    print("\n" + "=" * 60)
    print("  Training Complete")
    print("=" * 60)

    return metadata


# ═══════════════════════════════════════════
# INFERENCE
# ═══════════════════════════════════════════

_type_model = None
_risk_model = None
_type_enc = None
_risk_enc = None


def _load_models():
    """Lazy-load trained models."""
    global _type_model, _risk_model, _type_enc, _risk_enc
    if _type_model is None:
        if not os.path.exists(TYPE_MODEL_PATH):
            raise FileNotFoundError(
                "Models not trained yet. Run `python -m training.train_model` first."
            )
        _type_model = joblib.load(TYPE_MODEL_PATH)
        _risk_model = joblib.load(RISK_MODEL_PATH)
        _type_enc = joblib.load(TYPE_ENCODER_PATH)
        _risk_enc = joblib.load(RISK_ENCODER_PATH)


def predict_entry_type(text: str) -> dict:
    """Predict entry type and risk level for raw TPF text."""
    _load_models()
    features = extract_features(text).reshape(1, -1)

    type_pred = _type_model.predict(features)[0]
    type_proba = _type_model.predict_proba(features)[0]
    type_label = _type_enc.inverse_transform([type_pred])[0]
    type_confidence = float(max(type_proba))

    risk_pred = _risk_model.predict(features)[0]
    risk_proba = _risk_model.predict_proba(features)[0]
    risk_label = _risk_enc.inverse_transform([risk_pred])[0]
    risk_confidence = float(max(risk_proba))

    return {
        "entry_type": type_label,
        "entry_type_confidence": round(type_confidence, 4),
        "risk_level": risk_label,
        "risk_level_confidence": round(risk_confidence, 4),
        "feature_vector": extract_features(text).tolist(),
    }


# ═══════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════

if __name__ == "__main__":
    train()
