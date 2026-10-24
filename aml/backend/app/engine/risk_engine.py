from typing import Dict, Any
from ml.explainer import explainer

class HybridRiskAssessmentEngine:
    """Combines Rule, Behaviour, Graph, and XGBoost ML outputs into a unified AML Meta Risk Score."""

    def calculate_meta_risk(
        self,
        rule_score: float,
        behaviour_score: float,
        graph_score: float,
        feature_dict: dict
    ) -> Dict[str, Any]:
        
        # Obtain XGBoost prediction & SHAP breakdown from Explainer
        shap_res = explainer.explain_transaction(feature_dict)
        ml_probability = shap_res["prediction_probability"] # 0 - 100

        # Weighted hybrid formula
        # Rule (30%), Behaviour (25%), Graph (25%), ML XGBoost (20%)
        meta_score = (rule_score * 0.30) + (behaviour_score * 0.25) + (graph_score * 0.25) + (ml_probability * 0.20)
        meta_score = round(min(100.0, max(0.0, meta_score)), 2)

        # Priority calculation
        if meta_score >= 80.0:
            priority = "CRITICAL"
        elif meta_score >= 60.0:
            priority = "HIGH"
        elif meta_score >= 35.0:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return {
            "meta_risk_score": meta_score,
            "priority": priority,
            "rule_risk": round(rule_score, 2),
            "behaviour_risk": round(behaviour_score, 2),
            "graph_risk": round(graph_score, 2),
            "ml_risk": round(ml_probability, 2),
            "shap_explanation": shap_res
        }

risk_engine = HybridRiskAssessmentEngine()
