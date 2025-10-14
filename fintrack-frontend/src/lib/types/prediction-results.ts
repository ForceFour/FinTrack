/**
 * Type definitions for Prediction Results
 * Matches the Supabase database schema
 */

export type PredictionStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "partial";

export type WorkflowMode =
  | "full_pipeline"
  | "quick_classification"
  | "ingestion_only"
  | "validation_only"
  | "background_processing";

export type ProcessingStage =
  | "initial"
  | "nl_processing"
  | "ingestion"
  | "ner_extraction"
  | "classification"
  | "pattern_analysis"
  | "suggestion"
  | "safety_guard"
  | "validation"
  | "completed"
  | "error";

export interface CategoryProbabilities {
  [category: string]: number;
}

export interface ExtractedEntity {
  type: string;
  value: string;
  confidence: number;
  start_pos?: number;
  end_pos?: number;
}

export interface ExtractedEntities {
  merchants?: ExtractedEntity[];
  locations?: ExtractedEntity[];
  dates?: ExtractedEntity[];
  amounts?: ExtractedEntity[];
  [key: string]: ExtractedEntity[] | undefined;
}

export interface PatternInsight {
  insight_type: string;
  category?: string;
  description: string;
  severity: "low" | "medium" | "high";
  transactions_involved: string[];
  metadata?: Record<string, unknown>;
}

export interface SpendingPattern {
  pattern_type: string;
  frequency?: string;
  average_amount?: number;
  merchants?: string[];
  categories?: string[];
  confidence: number;
  metadata?: Record<string, unknown>;
}

export interface BudgetRecommendation {
  category: string;
  recommended_limit: number;
  current_spending: number;
  potential_savings: number;
  priority: "low" | "medium" | "high";
  reasoning: string;
}

export interface SpendingSuggestion {
  suggestion_type: string;
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
  potential_savings?: number;
  action_required: boolean;
  metadata?: Record<string, unknown>;
}

export interface SavingsOpportunity {
  opportunity_type: string;
  title: string;
  description: string;
  potential_monthly_savings: number;
  difficulty: "easy" | "medium" | "hard";
  category?: string;
}

export interface SecurityAlert {
  alert_type: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  transaction_id?: string;
  risk_score: number;
  recommended_action: string;
  timestamp: string;
}

export interface RiskAssessment {
  overall_risk_level: "low" | "medium" | "high" | "critical";
  risk_factors: string[];
  anomaly_details?: Record<string, unknown>;
  recommendation: string;
}

export interface ValidationError {
  field: string;
  error: string;
  severity: "warning" | "error";
}

export interface ProcessingHistoryEntry {
  stage: ProcessingStage;
  timestamp: string;
  status: "started" | "completed" | "failed";
  duration_ms?: number;
  confidence?: number;
  message?: string;
  metadata?: Record<string, unknown>;
}

export interface ConfidenceScore {
  stage: ProcessingStage;
  confidence: number;
  timestamp: string;
}

export interface ErrorLogEntry {
  stage: ProcessingStage;
  error: string;
  error_type: string;
  timestamp: string;
  stack_trace?: string;
}

export interface StageTimings {
  [stage: string]: number; // milliseconds
}

export interface AgentPerformance {
  agent_name: string;
  execution_time_ms: number;
  confidence: number;
  success: boolean;
  metadata?: Record<string, unknown>;
}

export interface FinalTransaction {
  id: string;
  amount: number;
  description: string;
  date: string;
  category?: string;
  merchant?: string;
  transaction_type: "income" | "expense" | "transfer";
  workflow_id?: string;
  predicted_category?: string;
  ner_entities?: ExtractedEntities;
  confidence_score?: number;
}

/**
 * Main Prediction Result interface
 * Matches the prediction_results table schema
 */
export interface PredictionResult {
  // Primary identification
  id: string;
  workflow_id: string;

  // Foreign keys
  user_id: string;
  transaction_id?: string | null;

  // Workflow metadata
  workflow_mode: WorkflowMode;
  status: PredictionStatus;
  current_stage?: ProcessingStage;

  // Input data
  user_input?: string | null;
  input_type?: string | null;
  raw_transaction_count?: number;

  // Classification results
  predicted_category?: string | null;
  category_confidence?: number | null;
  category_probabilities?: CategoryProbabilities | null;
  transaction_type?: string | null;
  transaction_type_confidence?: number | null;

  // Merchant extraction (NER) results
  merchant_name?: string | null;
  merchant_standardized?: string | null;
  merchant_category?: string | null;
  is_merchant_known?: boolean;
  merchant_confidence?: number | null;
  extracted_entities?: ExtractedEntities | null;

  // Pattern analysis results
  spending_patterns?: SpendingPattern[] | null;
  pattern_insights?: PatternInsight[] | null;
  recurring_transactions?: Record<string, unknown>[] | null;
  anomalies_detected?: Record<string, unknown>[] | null;
  pattern_confidence?: number | null;

  // Suggestions and recommendations
  budget_recommendations?: BudgetRecommendation[] | null;
  spending_suggestions?: SpendingSuggestion[] | null;
  savings_opportunities?: SavingsOpportunity[] | null;
  suggestion_confidence?: number | null;
  potential_monthly_savings?: number | null;

  // Security and safety results
  security_alerts?: SecurityAlert[] | null;
  risk_assessment?: RiskAssessment | null;
  fraud_score?: number | null;
  anomaly_score?: number | null;
  safety_confidence?: number | null;
  requires_human_review?: boolean;

  // Validation results
  validation_errors?: ValidationError[] | null;
  data_quality_score?: number | null;
  is_valid?: boolean;

  // Processing metadata
  processing_history?: ProcessingHistoryEntry[] | null;
  confidence_scores?: ConfidenceScore[] | null;
  error_log?: ErrorLogEntry[] | null;
  retry_count?: number;

  // Performance metrics
  total_processing_time?: number | null;
  stage_timings?: StageTimings | null;
  agent_performance?: AgentPerformance[] | null;

  // Final processed transaction
  final_transaction?: FinalTransaction | null;

  // Timestamps
  started_at: string;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Insert type for creating new prediction results
 */
export type PredictionResultInsert = Omit<
  PredictionResult,
  "id" | "created_at" | "updated_at"
> & {
  id?: string;
  created_at?: string;
  updated_at?: string;
};

/**
 * Update type for modifying prediction results
 */
export type PredictionResultUpdate = Partial<
  Omit<PredictionResult, "id" | "workflow_id" | "created_at">
>;

/**
 * View types for common queries
 */
export interface ActivePredictionWorkflow {
  id: string;
  workflow_id: string;
  user_id: string;
  workflow_mode: WorkflowMode;
  status: PredictionStatus;
  current_stage?: ProcessingStage;
  raw_transaction_count?: number;
  started_at: string;
  duration_seconds: number;
  overall_confidence?: number;
}

export interface CompletedPredictionSummary {
  id: string;
  workflow_id: string;
  user_id: string;
  workflow_mode: WorkflowMode;
  predicted_category?: string | null;
  category_confidence?: number | null;
  transaction_type?: string | null;
  merchant_standardized?: string | null;
  is_merchant_known?: boolean;
  overall_confidence?: number;
  fraud_score?: number | null;
  anomaly_score?: number | null;
  requires_human_review?: boolean;
  total_processing_time?: number | null;
  completed_at?: string | null;
  created_at: string;
}

export interface FailedPrediction {
  id: string;
  workflow_id: string;
  user_id: string;
  workflow_mode: WorkflowMode;
  current_stage?: ProcessingStage;
  error_log?: ErrorLogEntry[] | null;
  retry_count?: number;
  started_at: string;
  updated_at: string;
}

export interface HighRiskPrediction {
  id: string;
  workflow_id: string;
  user_id: string;
  predicted_category?: string | null;
  merchant_name?: string | null;
  fraud_score?: number | null;
  anomaly_score?: number | null;
  security_alerts?: SecurityAlert[] | null;
  requires_human_review?: boolean;
  completed_at?: string | null;
}

/**
 * Function return types
 */
export interface UserPredictionStats {
  total_predictions: number;
  completed_predictions: number;
  failed_predictions: number;
  avg_confidence?: number;
  avg_processing_time?: number;
  high_risk_count: number;
}

export interface RecentPrediction {
  workflow_id: string;
  status: PredictionStatus;
  predicted_category?: string | null;
  category_confidence?: number | null;
  merchant_name?: string | null;
  overall_confidence?: number;
  completed_at?: string | null;
}
