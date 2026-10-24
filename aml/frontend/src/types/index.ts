export type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'OFFICER' | 'ANALYST';

export interface User {
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  role: UserRole;
}

export interface Transaction {
  tx_id: string;
  sender_account: string;
  receiver_account: string;
  amount: number;
  currency: string;
  channel: string;
  tx_type: string;
  location?: string;
  ip_address?: string;
  device_id?: string;
  timestamp: string;
  flagged_typology: string;
}

export interface SHAPContribution {
  feature: string;
  label: string;
  contribution: number;
  impact: 'CRITICAL_RISK' | 'HIGH_RISK' | 'MEDIUM_RISK' | 'LOW_RISK';
}

export interface SHAPExplanation {
  base_value: number;
  prediction_probability: number;
  shap_values: SHAPContribution[];
}

export interface Alert {
  alert_id: string;
  tx_id?: string;
  customer_id?: string;
  typology: string;
  rule_risk: number;
  behaviour_risk: number;
  graph_risk: number;
  ml_risk: number;
  meta_risk_score: number;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'PENDING' | 'UNDER_INVESTIGATION' | 'CLOSED' | 'ESCALATED' | 'FALSE_POSITIVE';
  assigned_to?: string;
  shap_explanation?: string;
  created_at: string;
}

export interface Case {
  case_id: string;
  title: string;
  lead_customer_id?: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'OPEN' | 'IN_REVIEW' | 'ESCALATED' | 'CLOSED_STR' | 'CLOSED_FALSE_POSITIVE';
  correlated_typologies?: string;
  meta_risk_score: number;
  assigned_investigator?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface STRReport {
  report_id: string;
  case_id: string;
  fiu_ref_number: string;
  narrative_summary: string;
  status: 'DRAFT' | 'APPROVED' | 'SUBMITTED';
  generated_by?: string;
  approved_by?: string;
  pdf_path?: string;
  created_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  owner: string;
  type: string;
  balance: number;
  status: string;
  risk_category: string;
  is_suspicious: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  amount: number;
  label: string;
}
