// Neo4j Cypher Schema & Graph Algorithm Queries for AML Fund Flow Tracking

// 1. CONSTRAINTS & INDEXES
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT account_num_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE;
CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT ip_address_unique IF NOT EXISTS FOR (i:IP) REQUIRE i.address IS UNIQUE;

CREATE INDEX tx_timestamp_idx IF NOT EXISTS FOR ()-[r:TRANSFERRED]-() ON (r.timestamp);
CREATE INDEX tx_id_idx IF NOT EXISTS FOR ()-[r:TRANSFERRED]-() ON (r.tx_id);

// 2. GRAPH METRIC CALCULATIONS & QUERY LIBRARY

// Query A: Calculate Degree Centrality, Fan-In, Fan-Out for an Account
// MATCH (a:Account {account_number: $acc_num})
// OPTIONAL MATCH (in_acc:Account)-[r_in:TRANSFERRED]->(a)
// OPTIONAL MATCH (a)-[r_out:TRANSFERRED]->(out_acc:Account)
// RETURN a.account_number AS account,
//        count(DISTINCT in_acc) AS fan_in_count,
//        sum(r_in.amount) AS total_incoming,
//        count(DISTINCT out_acc) AS fan_out_count,
//        sum(r_out.amount) AS total_outgoing;

// Query B: Detect Circular Round Tripping (Hop Count 2 to 5)
// MATCH path = (a:Account {account_number: $acc_num})-[r:TRANSFERRED*2..5]->(a)
// WHERE ALL(idx in range(0, size(relationships(path))-2)
//       WHERE (relationships(path)[idx]).timestamp <= (relationships(path)[idx+1]).timestamp)
// RETURN path, [node in nodes(path) | node.account_number] AS node_chain,
//        [rel in relationships(path) | rel.amount] AS amounts;

// Query C: Detect Structuring / Smurfing Patterns (Fan-In Aggregation)
// MATCH (sender:Account)-[r:TRANSFERRED]->(receiver:Account {account_number: $receiver_acc})
// WHERE r.amount < 500000.0 AND r.timestamp >= $window_start
// WITH receiver, count(DISTINCT sender) as sender_count, sum(r.amount) as aggregate_amount, collect(sender.account_number) as senders
// WHERE sender_count >= 5
// RETURN receiver.account_number, sender_count, aggregate_amount, senders;

// Query D: Money Retention Ratio Calculation
// MATCH (a:Account {account_number: $acc_num})
// OPTIONAL MATCH (in_acc)-[r_in:TRANSFERRED]->(a) WHERE r_in.timestamp >= $window_start
// OPTIONAL MATCH (a)-[r_out:TRANSFERRED]->(out_acc) WHERE r_out.timestamp >= $window_start
// WITH coalesce(sum(r_in.amount), 0.0) as total_in, coalesce(sum(r_out.amount), 0.0) as total_out
// RETURN CASE WHEN total_in = 0 THEN 0 ELSE (total_in - total_out) / total_in END AS retention_ratio;

// Query E: Multi-hop Fund Flow Tracing (Source to Sink)
// MATCH path = (src:Account {account_number: $source_acc})-[r:TRANSFERRED*1..6]->(sink:Account {account_number: $sink_acc})
// RETURN path, nodes(path) as path_nodes, relationships(path) as path_rels;
