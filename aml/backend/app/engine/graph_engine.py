from typing import Dict, Any
from app.core.neo4j_client import in_memory_graph, is_neo4j_connected, run_cypher_query

class GraphIntelligenceEngine:
    """Computes network graph topological metrics for money flow paths."""

    def evaluate_graph_topology(self, sender: str, receiver: str, amount: float, tx_id: str, timestamp: str) -> Dict[str, Any]:
        # Sync live transaction into graph network
        in_memory_graph.add_transaction(sender, receiver, amount, tx_id, timestamp)
        
        # Calculate graph metrics for sender & receiver
        sender_metrics = in_memory_graph.get_metrics(sender)
        receiver_metrics = in_memory_graph.get_metrics(receiver)

        graph_risk_points = 0.0
        graph_anomalies = []

        # High Centrality / Fan-in Aggregator (Smurfing/Mule)
        if receiver_metrics["fan_in_count"] >= 4:
            graph_risk_points += 30.0
            graph_anomalies.append(f"Receiver account {receiver} is a high-degree fan-in aggregator ({receiver_metrics['fan_in_count']} unique senders)")

        # Low Retention Pass-Through (Layering Mule)
        if receiver_metrics["money_retention_ratio"] < 0.15 and receiver_metrics["total_outgoing"] > 100000.0:
            graph_risk_points += 35.0
            graph_anomalies.append(f"Receiver account {receiver} exhibits low money retention ({receiver_metrics['money_retention_ratio']*100:.0f}%) - Layering Mule signature")

        # Round Trip Cycle
        if sender_metrics["round_trip_detected"] or receiver_metrics["round_trip_detected"]:
            graph_risk_points += 40.0
            graph_anomalies.append("Closed circular round-tripping path detected across account graph")

        capped_graph_risk = min(100.0, graph_risk_points)

        return {
            "graph_risk_score": round(capped_graph_risk, 2),
            "degree_centrality": receiver_metrics["degree_centrality"],
            "betweenness_centrality": receiver_metrics["betweenness_centrality"],
            "money_retention_ratio": receiver_metrics["money_retention_ratio"],
            "hop_count": receiver_metrics["hop_count_max"],
            "round_trip_detected": sender_metrics["round_trip_detected"] or receiver_metrics["round_trip_detected"],
            "graph_anomalies": graph_anomalies
        }

graph_engine = GraphIntelligenceEngine()
