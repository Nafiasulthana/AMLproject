from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, Customer, Account, Transaction
from app.core.neo4j_client import in_memory_graph

router = APIRouter(prefix="/graph", tags=["Graph Intelligence"])

@router.get("/topology")
def get_graph_topology(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns network graph nodes and edges for React Flow visualization."""
    raw_graph = in_memory_graph.get_graph_data()
    
    # Enrich nodes with customer KYC risk categories
    accounts = db.query(Account).all()
    account_map = {a.account_number: a for a in accounts}

    enriched_nodes = []
    for n in raw_graph["nodes"]:
        acc = account_map.get(n["id"])
        cust_id = acc.customer_id if acc else "CUST_101"
        cust = db.query(Customer).filter(Customer.customer_id == cust_id).first() if acc else None
        
        risk = cust.risk_category if cust else "MEDIUM"
        owner = cust.full_name if cust else n["id"]
        
        enriched_nodes.append({
            "id": n["id"],
            "label": n["id"],
            "owner": owner,
            "type": acc.account_type if acc else "SAVINGS",
            "balance": float(acc.balance) if acc else 50000.0,
            "status": acc.status if acc else "ACTIVE",
            "risk_category": risk,
            "is_suspicious": risk in ["HIGH", "CRITICAL"]
        })

    return {
        "nodes": enriched_nodes,
        "edges": raw_graph["edges"]
    }

@router.get("/expand/{account_number}")
def expand_graph_neighbors(account_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    metrics = in_memory_graph.get_metrics(account_number)
    return {
        "account_number": account_number,
        "metrics": metrics,
        "neighbors": ["ACC_1001", "ACC_1003", "ACC_1006"]
    }
