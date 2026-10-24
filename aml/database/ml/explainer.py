import os
import json
import math
import logging
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

ALPHA = 0.7  # XGBoost-dominant blend

# Human-readable labels for each feature
_FEATURE_LABELS = {
    "amount":                  "Transaction Amount",
    "z_score_amount":          "Volume Z-Score Spike",
    "degree_centrality":       "Node Centrality Degree",
    "betweenness_centrality":  "Betweenness Centrality",
    "money_retention_ratio":   "Money Retention Ratio",
    "hop_count":               "Fund-Flow Hop Count",
    "structuring_flag":        "CTR Structuring Threshold Match",
    "layering_flag":           "Rapid Multi-Account Pass-Through",
    "round_trip_flag":         "Circular Round-Trip Cycle Detected",
    "dormant_flag":            "Dormant Account Reactivation",
    "smurfing_flag":           "Smurfing Pattern Detected",
    "high_risk_flag_count":    "High-Risk AML Rule Count",
    "risk_flag_any":           "Rule Violations Flagged",
    "z_score_retention_ratio": "Volume-to-Retention Ratio",
    "unretained_amount":       "Unretained Dollar Flow",
    "graph_activity_score":    "Graph Activity Score",
    "velocity_pass_through":   "Multihop Pass-Through Velocity",
}


def _shap_impact(contribution_pct: float) -> str:
    """Map a SHAP contribution (in percentage-point units) to an impact label."""
    abs_val = abs(contribution_pct)
    if abs_val >= 20.0:
        return "CRITICAL_RISK" if contribution_pct > 0 else "LOW_RISK"
    elif abs_val >= 10.0:
        return "HIGH_RISK" if contribution_pct > 0 else "LOW_RISK"
    elif abs_val >= 3.0:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"


def _build_real_shap_contributions(
    feature_names: list,
    raw_shap_values: np.ndarray,
    pred_prob: float,
) -> list:
    """Convert raw SHAP values to API contribution format."""
    contributions = []
    for feat, shap_v in zip(feature_names, raw_shap_values):
        contribution_pct = round(float(shap_v) * pred_prob * 100, 1)
        if abs(contribution_pct) < 0.3:
            continue
        label = _FEATURE_LABELS.get(feat, feat)
        contributions.append({
            "feature":      feat,
            "label":        label,
            "contribution": contribution_pct,
            "impact":       _shap_impact(contribution_pct),
        })
    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    return contributions


def _engineer_feature_dict(feature_dict: dict) -> dict:
    """Engineers derived domain features dynamically for inference."""
    fd = dict(feature_dict)
    flag_cols = ["structuring_flag", "layering_flag", "round_trip_flag", "dormant_flag", "smurfing_flag"]
    high_risk_cnt = sum(float(fd.get(c, 0)) for c in flag_cols)
    fd["high_risk_flag_count"] = high_risk_cnt
    fd["risk_flag_any"] = 1.0 if high_risk_cnt > 0 else 0.0
    
    z_score = float(fd.get("z_score_amount", 0.0))
    retention = float(fd.get("money_retention_ratio", 1.0))
    amount = float(fd.get("amount", 0.0))
    deg = float(fd.get("degree_centrality", 0.0))
    betweenness = float(fd.get("betweenness_centrality", 0.0))
    hop = float(fd.get("hop_count", 1.0))
    
    fd["z_score_retention_ratio"] = z_score / (retention + 0.01)
    fd["unretained_amount"] = amount * (1.0 - retention)
    fd["graph_activity_score"] = deg * betweenness
    fd["velocity_pass_through"] = (betweenness * z_score) / (hop + 1.0)
    return fd


class AMLExplainer:
    """SHAP and Feature Importance Explainer with Threshold Optimization for XGBoost AML Risk Model."""

    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_dir = os.path.abspath(model_dir)
        self.model = None
        self._iso_model = None
        self._anomaly_range = None
        self._shap_explainer = None
        self.optimal_threshold = 0.50
        self.feature_names = [
            "amount", "z_score_amount", "degree_centrality", "betweenness_centrality",
            "money_retention_ratio", "hop_count", "structuring_flag", "layering_flag",
            "round_trip_flag", "dormant_flag", "smurfing_flag", "high_risk_flag_count",
            "risk_flag_any", "z_score_retention_ratio", "unretained_amount",
            "graph_activity_score", "velocity_pass_through"
        ]
        self.load_model(model_dir=self.model_dir, raise_if_missing=False)

    def load_model(self, model_dir: str = None, raise_if_missing: bool = False):
        if model_dir is not None:
            self.model_dir = os.path.abspath(model_dir)

        model_path = os.path.join(self.model_dir, "xgboost_aml.json")
        meta_path  = os.path.join(self.model_dir, "model_metadata.json")
        feat_meta_path = os.path.join(self.model_dir, "feature_metadata.json")
        iso_path   = os.path.join(self.model_dir, "isolation_forest.pkl")

        self.model = None
        self._iso_model = None
        self._anomaly_range = None
        self._shap_explainer = None
        self.optimal_threshold = 0.50

        if not os.path.exists(model_path):
            msg = f"XGBoost model not found at {model_path}. Please train the model first."
            if raise_if_missing:
                logger.error(msg)
                raise FileNotFoundError(msg)
            else:
                logger.warning("%s — using fallback", msg)
                return False

        loaded_meta_features = None
        for path in (meta_path, feat_meta_path):
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        meta = json.load(f)
                        if not loaded_meta_features:
                            loaded_meta_features = meta.get("features") or meta.get("feature_names")
                            if loaded_meta_features:
                                self.feature_names = list(loaded_meta_features)
                        if "anomaly_score_range" in meta:
                            self._anomaly_range = meta["anomaly_score_range"]
                        if "optimal_threshold" in meta:
                            self.optimal_threshold = float(meta["optimal_threshold"])
                except Exception as exc:
                    logger.warning("Could not parse metadata file %s: %s", path, exc)

        if os.path.exists(iso_path) and self._anomaly_range is not None:
            try:
                self._iso_model = joblib.load(iso_path)
            except Exception as exc:
                logger.warning("Could not load IsolationForest model from %s: %s", iso_path, exc)

        try:
            from xgboost import XGBClassifier
            model = XGBClassifier()
            model.load_model(model_path)
            self.model = model
            logger.info("XGBoost AML model loaded successfully from %s (%d features, threshold=%.2f)",
                        model_path, len(self.feature_names), self.optimal_threshold)
        except Exception as exc:
            msg = f"Failed to load XGBoost model from {model_path}: {exc}"
            if raise_if_missing:
                logger.error(msg)
                raise RuntimeError(msg) from exc
            else:
                logger.error(msg)
                self.model = None
                return False

        self._get_shap_explainer()
        return True

    def _get_shap_explainer(self):
        if self._shap_explainer is None and self.model is not None:
            try:
                import shap
                self._shap_explainer = shap.TreeExplainer(self.model)
            except Exception as exc:
                logger.error("Could not build shap.TreeExplainer: %s", exc)
        return self._shap_explainer

    def _anomaly_score(self, df_input: pd.DataFrame) -> float:
        if self._iso_model is None or not self._anomaly_range:
            return 0.0
        try:
            raw = float(self._iso_model.decision_function(df_input)[0])
            iso_min = float(self._anomaly_range.get("min", 0.0))
            iso_max = float(self._anomaly_range.get("max", 1.0))
            if iso_max == iso_min:
                return 0.0
            return float(np.clip((iso_max - raw) / (iso_max - iso_min), 0.0, 1.0))
        except Exception:
            return 0.0

    def explain_transaction(self, feature_dict: dict) -> dict:
        model_used = self.model is not None

        # Engineer derived features dynamically
        full_feature_dict = _engineer_feature_dict(feature_dict)

        X = np.array(
            [[full_feature_dict.get(f, 0.0) for f in self.feature_names]],
            dtype=np.float32,
        )
        df_input = pd.DataFrame(X, columns=self.feature_names)

        if model_used:
            try:
                pred_prob = float(self.model.predict_proba(df_input)[0, 1])
            except Exception as exc:
                logger.error("predict_proba failed: %s", exc)
                model_used = False

        if not model_used:
            pred_prob = 0.50

        anomaly_score = self._anomaly_score(df_input)
        final_prob = ALPHA * pred_prob + (1 - ALPHA) * anomaly_score
        prediction_probability = round(final_prob * 100, 1)

        is_suspicious = pred_prob >= self.optimal_threshold

        base_value = 5.0
        if model_used:
            shap_ex = self._get_shap_explainer()
            if shap_ex is not None:
                try:
                    raw_shap = shap_ex.shap_values(df_input)
                    if isinstance(raw_shap, list):
                        raw_shap = raw_shap[1]
                    raw_shap_row = np.asarray(raw_shap[0])
                    exp_val = shap_ex.expected_value
                    if isinstance(exp_val, (list, np.ndarray)):
                        exp_val = exp_val[0]
                    base_prob = 1 / (1 + math.exp(-float(exp_val)))
                    base_value = round(base_prob * 100, 1)
                    contributions = _build_real_shap_contributions(
                        self.feature_names, raw_shap_row, pred_prob
                    )
                except Exception as exc:
                    logger.error("SHAP computation failed: %s", exc)
                    contributions = []
            else:
                contributions = []
        else:
            contributions = []

        return {
            "base_value":             base_value,
            "prediction_probability": prediction_probability,
            "xgb_probability":        round(pred_prob * 100, 1),
            "optimal_threshold":      round(self.optimal_threshold * 100, 1),
            "is_suspicious":          is_suspicious,
            "anomaly_score":           round(anomaly_score * 100, 1),
            "shap_values":            contributions,
            "model_used":             model_used,
        }


explainer = AMLExplainer()
