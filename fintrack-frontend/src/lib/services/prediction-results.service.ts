/**
 * Prediction Results Service
 * Service layer for interacting with the prediction_results table
 */

import { supabase } from "../supabase";
import type {
  PredictionResult,
  PredictionResultInsert,
  PredictionResultUpdate,
  ActivePredictionWorkflow,
  CompletedPredictionSummary,
  FailedPrediction,
  HighRiskPrediction,
  UserPredictionStats,
  RecentPrediction,
  PredictionStatus,
  WorkflowMode,
} from "../types/prediction-results";

/**
 * Service for managing prediction results
 */
export class PredictionResultsService {
  /**
   * Create a new prediction result
   */
  static async create(data: PredictionResultInsert) {
    const { data: result, error } = await supabase
      .from("prediction_results")
      .insert(data)
      .select()
      .single();

    if (error) throw error;
    return result as PredictionResult;
  }

  /**
   * Get a prediction result by ID
   */
  static async getById(id: string) {
    const { data, error } = await supabase
      .from("prediction_results")
      .select("*")
      .eq("id", id)
      .single();

    if (error) throw error;
    return data as PredictionResult;
  }

  /**
   * Get a prediction result by workflow ID
   */
  static async getByWorkflowId(workflowId: string) {
    const { data, error } = await supabase
      .from("prediction_results")
      .select("*")
      .eq("workflow_id", workflowId)
      .single();

    if (error) throw error;
    return data as PredictionResult;
  }

  /**
   * Update a prediction result
   */
  static async update(id: string, updates: PredictionResultUpdate) {
    const { data, error } = await supabase
      .from("prediction_results")
      .update(updates)
      .eq("id", id)
      .select()
      .single();

    if (error) throw error;
    return data as PredictionResult;
  }

  /**
   * Delete a prediction result
   */
  static async delete(id: string) {
    const { error } = await supabase
      .from("prediction_results")
      .delete()
      .eq("id", id);

    if (error) throw error;
  }

  /**
   * Get all prediction results for a user
   */
  static async getUserPredictions(userId: string, limit = 50, offset = 0) {
    const { data, error, count } = await supabase
      .from("prediction_results")
      .select("*", { count: "exact" })
      .eq("user_id", userId)
      .order("created_at", { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    return { results: data as PredictionResult[], total: count || 0 };
  }

  /**
   * Get predictions by status
   */
  static async getByStatus(status: PredictionStatus, limit = 50) {
    const { data, error } = await supabase
      .from("prediction_results")
      .select("*")
      .eq("status", status)
      .order("created_at", { ascending: false })
      .limit(limit);

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get active workflows (pending or processing)
   */
  static async getActiveWorkflows(userId?: string) {
    let query = supabase.from("active_prediction_workflows").select("*");

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as ActivePredictionWorkflow[];
  }

  /**
   * Get completed predictions summary
   */
  static async getCompletedSummary(userId?: string, limit = 50) {
    let query = supabase
      .from("completed_predictions_summary")
      .select("*")
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as CompletedPredictionSummary[];
  }

  /**
   * Get failed predictions
   */
  static async getFailedPredictions(userId?: string, limit = 50) {
    let query = supabase.from("failed_predictions").select("*").limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as FailedPrediction[];
  }

  /**
   * Get high-risk predictions
   */
  static async getHighRiskPredictions(userId?: string, limit = 50) {
    let query = supabase.from("high_risk_predictions").select("*").limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as HighRiskPrediction[];
  }

  /**
   * Get user prediction statistics
   */
  static async getUserStats(userId: string) {
    const { data, error } = await supabase.rpc("get_user_prediction_stats", {
      p_user_id: userId,
    });

    if (error) throw error;
    return data?.[0] as UserPredictionStats;
  }

  /**
   * Get recent predictions for a user
   */
  static async getRecentPredictions(userId: string, limit = 10) {
    const { data, error } = await supabase.rpc("get_recent_predictions", {
      p_user_id: userId,
      p_limit: limit,
    });

    if (error) throw error;
    return data as RecentPrediction[];
  }

  /**
   * Search predictions by merchant
   */
  static async searchByMerchant(
    merchantName: string,
    userId?: string,
    limit = 50
  ) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .or(
        `merchant_name.ilike.%${merchantName}%,merchant_standardized.ilike.%${merchantName}%`
      )
      .order("created_at", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Search predictions by category
   */
  static async searchByCategory(category: string, userId?: string, limit = 50) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .eq("predicted_category", category)
      .order("created_at", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get predictions requiring human review
   */
  static async getRequiringReview(userId?: string, limit = 50) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .eq("requires_human_review", true)
      .eq("status", "completed")
      .order("completed_at", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Filter predictions by workflow mode
   */
  static async getByWorkflowMode(
    mode: WorkflowMode,
    userId?: string,
    limit = 50
  ) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .eq("workflow_mode", mode)
      .order("created_at", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get predictions within date range
   */
  static async getByDateRange(
    startDate: Date,
    endDate: Date,
    userId?: string,
    limit = 100
  ) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .gte("created_at", startDate.toISOString())
      .lte("created_at", endDate.toISOString())
      .order("created_at", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get predictions with high confidence (>= threshold)
   */
  static async getHighConfidence(threshold = 0.8, userId?: string, limit = 50) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .gte("category_confidence", threshold)
      .order("category_confidence", { ascending: false })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get predictions with low confidence (< threshold) requiring review
   */
  static async getLowConfidence(threshold = 0.5, userId?: string, limit = 50) {
    let query = supabase
      .from("prediction_results")
      .select("*")
      .lt("category_confidence", threshold)
      .eq("status", "completed")
      .order("category_confidence", { ascending: true })
      .limit(limit);

    if (userId) {
      query = query.eq("user_id", userId);
    }

    const { data, error } = await query;

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Subscribe to real-time changes for a user's predictions
   */
  static subscribeToUserPredictions(
    userId: string,
    callback: (payload: {
      eventType: "INSERT" | "UPDATE" | "DELETE";
      new: PredictionResult;
      old: PredictionResult;
    }) => void
  ) {
    return supabase
      .channel("prediction_results_changes")
      .on(
        "postgres_changes" as never,
        {
          event: "*",
          schema: "public",
          table: "prediction_results",
          filter: `user_id=eq.${userId}`,
        } as never,
        callback as never
      )
      .subscribe();
  }

  /**
   * Subscribe to active workflow changes
   */
  static subscribeToActiveWorkflows(
    userId: string,
    callback: (payload: {
      eventType: "INSERT" | "UPDATE" | "DELETE";
      new: PredictionResult;
      old: PredictionResult;
    }) => void
  ) {
    return supabase
      .channel("active_workflows_changes")
      .on(
        "postgres_changes" as never,
        {
          event: "*",
          schema: "public",
          table: "prediction_results",
          filter: `user_id=eq.${userId}`,
        } as never,
        callback as never
      )
      .subscribe();
  }

  /**
   * Batch create prediction results
   */
  static async batchCreate(predictions: PredictionResultInsert[]) {
    const { data, error } = await supabase
      .from("prediction_results")
      .insert(predictions)
      .select();

    if (error) throw error;
    return data as PredictionResult[];
  }

  /**
   * Get aggregated statistics for a time period
   */
  static async getAggregatedStats(
    userId: string,
    startDate: Date,
    endDate: Date
  ) {
    const { data, error } = await supabase
      .from("prediction_results")
      .select(
        "status, workflow_mode, predicted_category, category_confidence, total_processing_time"
      )
      .eq("user_id", userId)
      .gte("created_at", startDate.toISOString())
      .lte("created_at", endDate.toISOString());

    if (error) throw error;

    // Calculate aggregations
    const results = data as PredictionResult[];
    return {
      total_predictions: results.length,
      by_status: this.groupBy(results, "status"),
      by_mode: this.groupBy(results, "workflow_mode"),
      by_category: this.groupBy(results, "predicted_category"),
      avg_confidence: this.average(
        results.map((r) => r.category_confidence || 0)
      ),
      avg_processing_time: this.average(
        results.map((r) => r.total_processing_time || 0)
      ),
    };
  }

  /**
   * Helper: Group by field
   */
  private static groupBy(
    array: PredictionResult[],
    field: keyof PredictionResult
  ) {
    return array.reduce((acc, item) => {
      const key = String(item[field] || "unknown");
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  /**
   * Helper: Calculate average
   */
  private static average(numbers: number[]) {
    if (numbers.length === 0) return 0;
    return numbers.reduce((a, b) => a + b, 0) / numbers.length;
  }
}

export default PredictionResultsService;
