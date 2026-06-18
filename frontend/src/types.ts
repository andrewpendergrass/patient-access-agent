export interface AgentStep {
  node: string;
  label: string;
  detail: string;
  status: "complete" | "emergency" | "pending";
}

export interface CaseSummary {
  chief_request: string;
  intent_category: string;
  risk_assessment: string;
  action_taken: string;
  resolution: string;
  follow_up_required: boolean;
  escalated: boolean;
  tags: string[];
}

export interface AgentResult {
  response: string;
  case_summary: CaseSummary;
  case_id: string;
  risk_level: string;
  intent: string;
  retrieved_data: Record<string, unknown>;
}

export interface Case {
  id: string;
  created_at: string;
  request: string;
  intent: string;
  risk_level: string;
  response: string;
  case_summary: CaseSummary;
  steps: AgentStep[];
}
