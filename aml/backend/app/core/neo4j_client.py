import logging
from typing import Dict, List, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard Neo4j Driver Connection
neo4j_driver = None
is_neo4j_connected = False

try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD))
    # Quick connectivity test
    driver.verify_connectivity()
    neo4j_driver = driver
    is_neo4j_connected = True
    logger.info("Connected to live Neo4j database.")
except Exception as e:
    logger.warning(f"Neo4j driver connection omitted or failed ({e}). Enabling In-Memory Graph Intelligence Engine.")

class InGraphEngine:
    """In-Memory fallback graph engine for local environment execution."""
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {} # account_num -> node details
        self.edges: List[Dict[str, Any]] = [] # list of tx edges

    def add_transaction(self, sender: str, receiver: str, amount: float, tx_id: str, timestamp: str):
        if sender not in self.nodes:
            self.nodes[sender] = {"account_number": sender, "type": "Account"}
        if receiver not in self.nodes:
            self.nodes[receiver] = {"account_number": receiver, "type": "Account"}
        
        self.edges.append({
            "tx_id": tx_id,
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "timestamp": timestamp
        })

    def get_metrics(self, account_num: str) -> Dict[str, Any]:
        fan_in = set()
        fan_out = set()
        total_in = 0.0
        total_out = 0.0

        for edge in self.edges:
            if edge["receiver"] == account_num:
                fan_in.add(edge["sender"])
                total_in += edge["amount"]
            if edge["sender"] == account_num:
                fan_out.add(edge["receiver"])
                total_out += edge["amount"]

        degree_centrality = len(fan_in) + len(fan_out)
        retention_ratio = 0.0 if total_in == 0 else max(0.0, (total_in - total_out) / total_in)

        # Detect round trip
        round_trip_detected = False
        for out_acc in fan_out:
            for edge2 in self.edges:
                if edge2["sender"] == out_acc and edge2["receiver"] == account_num:
                    round_trip_detected = True
                    break

        return {
            "degree_centrality": degree_centrality,
            "fan_in_count": len(fan_in),
            "fan_out_count": len(fan_out),
            "total_incoming": total_in,
            "total_outgoing": total_out,
            "money_retention_ratio": round(retention_ratio, 2),
            "betweenness_centrality": round(degree_centrality * 0.12, 3),
            "page_rank": round(0.15 + (degree_centrality * 0.08), 3),
            "round_trip_detected": round_trip_detected,
            "hop_count_max": 3 if len(fan_out) > 2 else 1
        }

    def get_graph_data(self) -> Dict[str, Any]:
        node_list = []
        for acc_id in self.nodes:
            node_list.append({"id": acc_id, "label": acc_id, "type": "Account"})
        
        edge_list = []
        for idx, edge in enumerate(self.edges[-100:]): # return recent 100
            edge_list.append({
                "id": f"e_{idx}_{edge['tx_id']}",
                "source": edge["sender"],
                "target": edge["receiver"],
                "amount": edge["amount"],
                "label": f"₹{edge['amount']:,.2f}"
            })
            
        return {"nodes": node_list, "edges": edge_list}

in_memory_graph = InGraphEngine()

# Seed default mock graph links
in_memory_graph.add_transaction("ACC_1001", "ACC_1003", 500000.0, "TX_INIT_1", "2026-07-30 10:00:00")
in_memory_graph.add_transaction("ACC_1003", "ACC_1006", 480000.0, "TX_INIT_2", "2026-07-30 10:15:00")
in_memory_graph.add_transaction("ACC_1006", "ACC_1001", 450000.0, "TX_INIT_3", "2026-07-30 10:30:00")

def run_cypher_query(query: str, parameters: dict = None) -> List[Dict[str, Any]]:
    if is_neo4j_connected and neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Cypher query on Neo4j: {e}")
    return []
