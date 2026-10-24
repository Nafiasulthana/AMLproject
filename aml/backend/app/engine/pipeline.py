import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Transaction, Account, Customer, CustomerBehaviourProfile, Alert
from app.engine.rule_engine import rule_engine
from app.engine.behaviour_engine import behaviour_engine
from app.engine.graph_engine import graph_engine
from app.engine.risk_engine import risk_engine
from app.engine.correlation_engine import correlation_engine

class AMLPipeline:
    """End-to-End AML Transaction Detection and Triaging Pipeline."""

    def process_transaction(self, tx_data: dict, db: Session) -> Dict[str, Any]:
        tx_id = tx_data.get("tx_id", f"TX_{uuid.uuid4().hex[:10].upper()}")
        sender_acc_num = tx_data.get("sender_account")
        receiver_acc_num = tx_data.get("receiver_account")
        amount = float(tx_data.get("amount", 0.0))

        # 1. Fetch Relational Context
        sender_acc = db.query(Account).filter(Account.account_number == sender_acc_num).first()
        receiver_acc = db.query(Account).filter(Account.account_number == receiver_acc_num).first()

        sender_cust = db.query(Customer).filter(Customer.customer_id == sender_acc.customer_id).first() if sender_acc else None
        receiver_cust = db.query(Customer).filter(Customer.customer_id == receiver_acc.customer_id).first() if receiver_acc else None

        customer = sender_cust or receiver_cust
        cust_id = customer.customer_id if customer else "CUST_DEFAULT"
        profile = db.query(CustomerBehaviourProfile).filter(CustomerBehaviourProfile.customer_id == cust_id).first() if customer else None

        # 2. Execute Rule Engine Stage
        rule_res = rule_engine.evaluate_transaction(tx_data, customer, sender_acc, db)

        # 3. Execute Behaviour Intelligence Engine Stage
        behaviour_res = behaviour_engine.evaluate_behaviour(tx_data, profile, customer)

        # 4. Execute Graph Intelligence Engine Stage
        ts_str = str(tx_data.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        graph_res = graph_engine.evaluate_graph_topology(sender_acc_num, receiver_acc_num, amount, tx_id, ts_str)

        # Prepare ML feature dict
        struct_flag = 1 if any(r["rule_code"] == "R_STRUCTURING" for r in rule_res["triggered_rules"]) else 0
        dorm_flag = 1 if any(r["rule_code"] == "R_DORMANT" for r in rule_res["triggered_rules"]) else 0
        layer_flag = 1 if tx_data.get("flagged_typology") in ["LAYERING", "MONEY_MULE"] else 0
        round_flag = 1 if graph_res["round_trip_detected"] else 0
        smurf_flag = 1 if tx_data.get("flagged_typology") == "SMURFING" else 0

        feature_dict = {
            "amount": amount,
            "z_score_amount": behaviour_res["z_score_amount"],
            "degree_centrality": graph_res["degree_centrality"],
            "betweenness_centrality": graph_res["betweenness_centrality"],
            "money_retention_ratio": graph_res["money_retention_ratio"],
            "hop_count": graph_res["hop_count"],
            "structuring_flag": struct_flag,
            "layering_flag": layer_flag,
            "round_trip_flag": round_flag,
            "dormant_flag": dorm_flag,
            "smurfing_flag": smurf_flag
        }

        # 5. Hybrid Meta Risk Assessment + XGBoost + SHAP Stage
        risk_res = risk_engine.calculate_meta_risk(
            rule_score=rule_res["rule_risk_score"],
            behaviour_score=behaviour_res["behaviour_risk_score"],
            graph_score=graph_res["graph_risk_score"],
            feature_dict=feature_dict
        )

        # Record Transaction
        db_tx = Transaction(
            tx_id=tx_id,
            sender_account=sender_acc_num,
            receiver_account=receiver_acc_num,
            amount=amount,
            channel=tx_data.get("channel", "NEFT"),
            tx_type=tx_data.get("tx_type", "TRANSFER"),
            location=tx_data.get("location", "Mumbai, India"),
            ip_address=tx_data.get("ip_address", "192.168.1.10"),
            device_id=tx_data.get("device_id", "DEV_99"),
            timestamp=datetime.utcnow(),
            flagged_typology=tx_data.get("flagged_typology", "NORMAL")
        )
        db.add(db_tx)
        db.commit()

        alert_obj = None
        case_obj = None

        # 6. Generate Alert & Case if Meta-Risk Score >= 35.0
        if risk_res["meta_risk_score"] >= 35.0:
            alert_id = f"ALT_{uuid.uuid4().hex[:8].upper()}"
            typology = tx_data.get("flagged_typology")
            if not typology or typology == "NORMAL":
                typology = rule_res["triggered_rules"][0]["rule_code"].replace("R_", "") if rule_res["triggered_rules"] else "BEHAVIOUR_SPIKE"

            alert_obj = Alert(
                alert_id=alert_id,
                tx_id=tx_id,
                customer_id=cust_id,
                typology=typology,
                rule_risk=risk_res["rule_risk"],
                behaviour_risk=risk_res["behaviour_risk"],
                graph_risk=risk_res["graph_risk"],
                ml_risk=risk_res["ml_risk"],
                meta_risk_score=risk_res["meta_risk_score"],
                priority=risk_res["priority"],
                status="PENDING",
                shap_explanation=json.dumps(risk_res["shap_explanation"]),
                created_at=datetime.utcnow()
            )
            db.add(alert_obj)
            db.commit()

            # 7. Execute Cross-Typology Correlation Engine
            case_obj = correlation_engine.correlate_alert_to_case(alert_obj, db)

        return {
            "tx_id": tx_id,
            "meta_risk_score": risk_res["meta_risk_score"],
            "priority": risk_res["priority"],
            "alert_generated": alert_obj is not None,
            "alert_id": alert_obj.alert_id if alert_obj else None,
            "case_id": case_obj.case_id if case_obj else None,
            "rule_details": rule_res,
            "behaviour_details": behaviour_res,
            "graph_details": graph_res,
            "shap_explanation": risk_res["shap_explanation"]
        }

pipeline = AMLPipeline()
