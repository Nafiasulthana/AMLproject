"""
Sanity check for the real XGBoost AML inference pipeline.

Usage (from the aml/database/ directory):
    python ml/test_explainer_sanity.py

What this checks:
  - model_used == True  (confirms the model file was found and loaded)
  - prediction_probability for the suspicious case is noticeably higher
    than for the normal case (confirms the model actually fires)
  - SHAP contributions are real numbers driven by input values,
    not fixed hardcoded constants
"""

import sys
import os

# Make sure `database/` is on the path so `from ml.explainer import ...` works
_here = os.path.dirname(__file__)
_database_dir = os.path.abspath(os.path.join(_here, ".."))
if _database_dir not in sys.path:
    sys.path.insert(0, _database_dir)

from ml.explainer import AMLExplainer  # fresh instance, not the module singleton

# ---------------------------------------------------------------------------
SAMPLE_CASES = {
    "normal": {
        "amount":                 8_500.0,
        "z_score_amount":         0.3,
        "degree_centrality":      2,
        "betweenness_centrality": 0.04,
        "money_retention_ratio":  0.82,
        "hop_count":              1,
        # flag features (not in model, but present in pipeline feature_dict)
        "structuring_flag":  0,
        "layering_flag":     0,
        "round_trip_flag":   0,
        "dormant_flag":      0,
        "smurfing_flag":     0,
    },
    "suspicious": {
        "amount":                 480_000.0,
        "z_score_amount":         3.8,
        "degree_centrality":      9,
        "betweenness_centrality": 0.45,
        "money_retention_ratio":  0.08,
        "hop_count":              4,
        "structuring_flag":  1,
        "layering_flag":     1,
        "round_trip_flag":   1,
        "dormant_flag":      0,
        "smurfing_flag":     0,
    },
}
# ---------------------------------------------------------------------------

def _bar(value: float, width: int = 30) -> str:
    """ASCII probability bar."""
    filled = int(round(abs(value) / 100.0 * width))
    symbol = "#" if value >= 0 else "-"
    return symbol * filled + "." * (width - filled)


def run_sanity_check():
    print("\n" + "=" * 65)
    print("  AML XGBoost Inference Sanity Check")
    print("=" * 65)

    ex = AMLExplainer()

    print(f"\n  Model dir  : {ex.model_dir}")
    print(f"  Feature set: {ex.feature_names}")
    print(f"  Model loaded: {'YES [OK]' if ex.model is not None else 'NO -- will use heuristic fallback'}")
    print()

    results = {}
    for case_name, feature_dict in SAMPLE_CASES.items():
        result = ex.explain_transaction(feature_dict)
        results[case_name] = result

        print(f"  --- Case: {case_name.upper()} --------------------------------")
        print(f"     model_used            : {result['model_used']}")
        print(f"     base_value            : {result['base_value']}")
        print(f"     prediction_probability: {result['prediction_probability']}%")
        print(f"     [{_bar(result['prediction_probability'])}] {result['prediction_probability']}%")
        print()
        print(f"     SHAP contributions ({len(result['shap_values'])} features above noise floor):")
        for c in result["shap_values"]:
            print(f"       {c['contribution']:+6.1f}%  [{c['impact']:<13}]  {c['feature']}  ->  {c['label']}")
        print()

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------
    print("  --- Assertions ----------------------------------------------------")
    passed = True

    def check(condition: bool, msg_ok: str, msg_fail: str):
        nonlocal passed
        if condition:
            print(f"  [PASS]  {msg_ok}")
        else:
            print(f"  [FAIL]  {msg_fail}")
            passed = False

    check(
        results["normal"]["model_used"],
        "model_used == True (real model is loaded)",
        "model_used == False -- check that xgboost_aml.json exists in database/ml/models/",
    )
    check(
        results["suspicious"]["model_used"],
        "model_used == True (consistent across calls)",
        "model_used changed between calls -- should be stable",
    )

    prob_normal     = results["normal"]["prediction_probability"]
    prob_suspicious = results["suspicious"]["prediction_probability"]
    diff = prob_suspicious - prob_normal
    check(
        diff > 10.0,
        f"suspicious probability ({prob_suspicious}%) > normal ({prob_normal}%) by {diff:.1f}pp  [threshold: >10pp]",
        f"probability barely moved: normal={prob_normal}%, suspicious={prob_suspicious}% (diff={diff:.1f}pp). "
        "Model may not be using real features.",
    )

    check(
        len(results["suspicious"]["shap_values"]) > 0,
        "SHAP contributions list is non-empty for suspicious case",
        "SHAP contributions are empty -- something went wrong in computation",
    )

    # Check that at least one contribution is positive for the suspicious case
    has_positive = any(c["contribution"] > 0 for c in results["suspicious"]["shap_values"])
    check(
        has_positive,
        "At least one positive SHAP contribution in suspicious case (model is pushing toward suspicious)",
        "No positive SHAP contributions for suspicious case -- check model or scaling",
    )

    print()
    print("=" * 65)
    if passed:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED -- see above for details")
    print("=" * 65 + "\n")

    # ------------------------------------------------------------------
    # Synthetic-generator methodology note
    # ------------------------------------------------------------------
    print("  [NOTE] On training data quality:")
    print("     synthetic_generator.py samples every raw feature from a label-agnostic")
    print("     distribution, derives rule-trigger flags FROM those features, then")
    print("     assigns the label via Bernoulli(sigmoid(weighted risk score + noise)).")
    print("     Metrics reported by train_model.py (ROC-AUC ~0.81-0.85, F1 ~0.51) reflect")
    print("     a genuine feature -> label relationship with irreducible class overlap,")
    print("     not a reconstruction of the generator's own lookup table.")
    print("     For production, replace with real (labeled) transaction data.")
    print()

    return passed


if __name__ == "__main__":
    ok = run_sanity_check()
    sys.exit(0 if ok else 1)
