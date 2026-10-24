from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models.models import AMLRule, Customer, Account, Transaction

class RuleEngine:
    """Evaluates transaction streams against configured AML rules."""

    def evaluate_transaction(self, tx_data: dict, customer: Customer, account: Account, db: Session) -> Dict[str, Any]:
        rules = db.query(AMLRule).filter(AMLRule.is_enabled == True).all()
        rule_map = {r.rule_code: r for r in rules}

        triggered_rules = []
        total_rule_score = 0.0

        amount = float(tx_data.get("amount", 0.0))
        flagged_typology = tx_data.get("flagged_typology", "NORMAL")

        # 1. Structuring Rule (< ₹500,000 / $10,000 threshold avoidance)
        if 480000.0 <= amount < 500000.0 or flagged_typology == "STRUCTURING":
            rule = rule_map.get("R_STRUCTURING")
            weight = float(rule.risk_weight) if rule else 35.0
            triggered_rules.append({
                "rule_code": "R_STRUCTURING",
                "name": "CTR Avoidance Structuring",
                "description": f"Transaction amount ₹{amount:,.2f} is just below ₹500,000 reporting threshold",
                "weight": weight
            })
            total_rule_score += weight

        # 2. Dormant Account Spike
        if account and account.status == "DORMANT" and amount > 50000.0 or flagged_typology == "DORMANT":
            rule = rule_map.get("R_DORMANT")
            weight = float(rule.risk_weight) if rule else 25.0
            triggered_rules.append({
                "rule_code": "R_DORMANT",
                "name": "Dormant Account Sudden Activity",
                "description": f"High value transaction ₹{amount:,.2f} on dormant account {account.account_number}",
                "weight": weight
            })
            total_rule_score += weight

        # 3. Profile Mismatch (Amount > 5x stated monthly income)
        monthly_inc = float(customer.monthly_income or 50000.0)
        if amount > (monthly_inc * 3.5) or flagged_typology == "PROFILE_MISMATCH":
            rule = rule_map.get("R_PROFILE_MISMATCH")
            weight = float(rule.risk_weight) if rule else 20.0
            triggered_rules.append({
                "rule_code": "R_PROFILE_MISMATCH",
                "name": "Customer Profile Income Mismatch",
                "description": f"Tx amount ₹{amount:,.2f} exceeds 3.5x declared monthly income ₹{monthly_inc:,.2f}",
                "weight": weight
            })
            total_rule_score += weight

        # 4. Layering / Money Mule
        if flagged_typology in ["LAYERING", "MONEY_MULE"]:
            rule = rule_map.get("R_LAYERING" if flagged_typology == "LAYERING" else "R_MONEY_MULE")
            weight = float(rule.risk_weight) if rule else 35.0
            triggered_rules.append({
                "rule_code": f"R_{flagged_typology}",
                "name": f"{flagged_typology.replace('_', ' ').title()} Pattern Flagged",
                "description": f"System simulation engine flagged {flagged_typology} topology pattern",
                "weight": weight
            })
            total_rule_score += weight

        # 5. Round Tripping
        if flagged_typology == "ROUND_TRIP":
            rule = rule_map.get("R_ROUNDTRIP")
            weight = float(rule.risk_weight) if rule else 40.0
            triggered_rules.append({
                "rule_code": "R_ROUNDTRIP",
                "name": "Circular Round Tripping Detected",
                "description": "Closed cycle money flow returned to initial source account",
                "weight": weight
            })
            total_rule_score += weight

        # 6. Smurfing
        if flagged_typology == "SMURFING":
            rule = rule_map.get("R_SMURFING")
            weight = float(rule.risk_weight) if rule else 30.0
            triggered_rules.append({
                "rule_code": "R_SMURFING",
                "name": "Multi-Sender Smurfing Aggregation",
                "description": "Consolidation of micro-deposits from multiple sender endpoints",
                "weight": weight
            })
            total_rule_score += weight

        capped_rule_score = min(100.0, total_rule_score)

        return {
            "triggered_rules": triggered_rules,
            "rule_risk_score": round(capped_rule_score, 2)
        }

rule_engine = RuleEngine()
