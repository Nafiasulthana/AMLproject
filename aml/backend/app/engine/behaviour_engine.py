import json
import numpy as np
from typing import Dict, Any
from app.models.models import CustomerBehaviourProfile, Customer

class BehaviourIntelligenceEngine:
    """Detects statistical deviations from historical customer behaviour profiles."""

    def evaluate_behaviour(self, tx_data: dict, profile: CustomerBehaviourProfile, customer: Customer) -> Dict[str, Any]:
        if not profile:
            return {"behaviour_risk_score": 10.0, "z_score": 0.0, "anomalies": []}

        amount = float(tx_data.get("amount", 0.0))
        avg_amt = float(profile.avg_transaction_amount or 5000.0)
        max_single = float(profile.max_single_tx_amount or 25000.0)
        
        # Estimate standard deviation (assumed 40% of average)
        std_dev = max(1000.0, avg_amt * 0.40)
        z_score = (amount - avg_amt) / std_dev

        anomalies = []
        risk_points = 0.0

        # Amount Z-score check
        if z_score > 3.0:
            risk_points += min(45.0, (z_score - 3.0) * 12.0)
            anomalies.append(f"Transaction amount is {z_score:.1f} standard deviations above historical mean")

        # Exceeds max historical single transaction amount
        if amount > max_single * 2.0:
            risk_points += 30.0
            anomalies.append(f"Amount ₹{amount:,.2f} is 2x+ greater than historical single max ₹{max_single:,.2f}")

        # Channel anomaly
        preferred_channels = json.loads(profile.preferred_channels) if profile.preferred_channels else ["UPI", "NEFT"]
        channel = tx_data.get("channel", "NEFT")
        if channel not in preferred_channels:
            risk_points += 15.0
            anomalies.append(f"Unusual channel '{channel}' used (Customer usually uses {preferred_channels})")

        capped_behaviour_score = min(100.0, risk_points)

        return {
            "behaviour_risk_score": round(capped_behaviour_score, 2),
            "z_score_amount": round(z_score, 2),
            "anomalies": anomalies
        }

behaviour_engine = BehaviourIntelligenceEngine()
