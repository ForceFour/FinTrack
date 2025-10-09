/**
 * Type definitions for FinTrack application
 */

export interface Transaction {
  id?: string;
  user_id?: string;
  amount: number;
  description: string;
  date: string;
  merchant?: string | null;
  category?: string | null;
  subcategory?: string | null;
  transaction_type: string; // Changed from union type to string to match Supabase
  status?: string;
  payment_method?: string | null;
  account_type?: string | null;
  confidence?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  created_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AgentStatus {
  ingestion: "idle" | "running" | "complete" | "error";
  ner_merchant: "idle" | "running" | "complete" | "error";
  classifier: "idle" | "running" | "complete" | "error";
  pattern_analyzer: "idle" | "running" | "complete" | "error";
  suggestion: "idle" | "running" | "complete" | "error";
  safety_guard: "idle" | "running" | "complete" | "error";
}

export interface SpendingAnalytics {
  total_spending: number;
  average_transaction: number;
  transaction_count: number;
  top_category: string;
  spending_trend: "increasing" | "decreasing" | "stable";
  period: string;
}

export interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
  transaction_count: number;
}

export interface Suggestion {
  type: "savings" | "budget" | "optimization" | "alert";
  title: string;
  description: string;
  potential_savings?: number;
  recommended_amount?: number;
  difficulty?: "Easy" | "Medium" | "Hard";
  priority?: "Low" | "Medium" | "High";
}

export interface WorkflowStatus {
  workflow_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  current_agent?: string;
  progress: number;
  start_time: string;
  end_time?: string;
  result?: Record<string, unknown>;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

export interface ConversationMessage {
  type: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ConversationContext {
  missing_fields?: string[];
  original_input?: string;
  current_field?: string;
  [key: string]: unknown;
}

export interface SecurityAlert {
  id: string;
  type: "fraud" | "anomaly" | "suspicious";
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  transaction_id?: string;
  timestamp: string;
  resolved: boolean;
}
