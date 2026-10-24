import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Case, Alert, Customer

class CrossTypologyCorrelationEngine:
    """Fuses multi-typology alerts across a customer network into unified Investigation Cases."""

    def correlate_alert_to_case(self, alert: Alert, db: Session) -> Case:
        # Check if an open case already exists for this lead customer
        existing_case = db.query(Case).filter(
            Case.lead_customer_id == alert.customer_id,
            Case.status.in_(["OPEN", "IN_REVIEW", "ESCALATED"])
        ).first()

        customer = db.query(Customer).filter(Customer.customer_id == alert.customer_id).first()
        cust_name = customer.full_name if customer else alert.customer_id

        if existing_case:
            # Correlate into existing case
            typologies = json.loads(existing_case.correlated_typologies or "[]")
            if alert.typology not in typologies:
                typologies.append(alert.typology)
                existing_case.correlated_typologies = json.dumps(typologies)

            # Update highest meta risk score
            if float(alert.meta_risk_score) > float(existing_case.meta_risk_score):
                existing_case.meta_risk_score = alert.meta_risk_score
                if float(alert.meta_risk_score) >= 80.0:
                    existing_case.priority = "CRITICAL"

            existing_case.summary = f"Multi-typology AML network pattern detected for {cust_name}: Correlated typologies {typologies}"
            existing_case.updated_at = datetime.utcnow()
            db.commit()
            return existing_case
        else:
            # Create a new investigation case
            case_id = f"CASE_{uuid.uuid4().hex[:8].upper()}"
            new_case = Case(
                case_id=case_id,
                title=f"AML Case: {alert.typology} - {cust_name}",
                lead_customer_id=alert.customer_id,
                priority=alert.priority,
                status="OPEN",
                correlated_typologies=json.dumps([alert.typology]),
                meta_risk_score=alert.meta_risk_score,
                summary=f"Automated AML Case opened following high risk alert ({alert.typology}) with Meta-Risk Score {alert.meta_risk_score}%",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_case)
            db.commit()
            return new_case

correlation_engine = CrossTypologyCorrelationEngine()
