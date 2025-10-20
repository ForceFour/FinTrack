/**
 * Workflow monitoring types
 * Maps to workflow service responses from backend
 */

export type WorkflowStatus = "pending" | "processing" | "completed" | "failed";

export interface WorkflowResult {
  transactions_processed: number;
  category?: string;
  merchant?: string;
  confidence?: number;
  insights_generated: number;
  suggestions_count: number;
}

export interface WorkflowStatusData {
  workflow_id: string;
  status: WorkflowStatus;
  current_agent?: string;
  progress: number;
  start_time: string;
  end_time?: string;
  source_name?: string; // File name or chat title
  result?: WorkflowResult;
}

export interface ProcessingLog {
  timestamp: string;
  file: string;
  source_name?: string; // Friendly display name
  transactions: number;
  status: string;
  workflow_id?: string;
}

export interface WorkflowStatistics {
  total: number;
  completed: number;
  processing: number;
  pending: number;
  failed: number;
}

export interface WorkflowStatisticsResponse {
  status: string;
  user_id: string;
  statistics: WorkflowStatistics;
  timestamp: string;
}

export interface ActiveWorkflowsResponse {
  status: string;
  user_id: string;
  workflows: WorkflowStatusData[];
  count: number;
  timestamp: string;
}

export interface WorkflowHistoryResponse {
  status: string;
  user_id: string;
  history: ProcessingLog[];
  count: number;
  timestamp: string;
}

export interface WorkflowDetailResponse {
  status: string;
  workflow: WorkflowStatusData;
  timestamp: string;
}

export interface AgentCommunication {
  timestamp: string;
  workflow_id: string;
  agent: string;
  stage: string;
  message: string;
  status: string;
  details?: Record<string, unknown>;
}

export interface AgentCommunicationsResponse {
  status: string;
  user_id: string;
  communications: AgentCommunication[];
  count: number;
  timestamp: string;
}
