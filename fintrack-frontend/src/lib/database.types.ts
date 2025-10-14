export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5";
  };
  public: {
    Tables: {
      prediction_results: {
        Row: {
          id: string;
          workflow_id: string;
          user_id: string;
          transaction_id: string | null;
          workflow_mode: string;
          status: string;
          current_stage: string | null;
          user_input: string | null;
          input_type: string | null;
          raw_transaction_count: number | null;
          duplicates_detected: number | null;
          duplicates_skipped: number | null;
          predicted_category: string | null;
          category_confidence: number | null;
          category_probabilities: Json | null;
          transaction_type: string | null;
          transaction_type_confidence: number | null;
          merchant_name: string | null;
          merchant_standardized: string | null;
          merchant_category: string | null;
          is_merchant_known: boolean | null;
          merchant_confidence: number | null;
          extracted_entities: Json | null;
          spending_patterns: Json | null;
          pattern_insights: Json | null;
          recurring_transactions: Json | null;
          anomalies_detected: Json | null;
          pattern_confidence: number | null;
          budget_recommendations: Json | null;
          spending_suggestions: Json | null;
          savings_opportunities: Json | null;
          suggestion_confidence: number | null;
          potential_monthly_savings: number | null;
          security_alerts: Json | null;
          risk_assessment: Json | null;
          fraud_score: number | null;
          anomaly_score: number | null;
          safety_confidence: number | null;
          requires_human_review: boolean | null;
          validation_errors: Json | null;
          data_quality_score: number | null;
          is_valid: boolean | null;
          processing_history: Json | null;
          confidence_scores: Json | null;
          error_log: Json | null;
          retry_count: number | null;
          total_processing_time: number | null;
          stage_timings: Json | null;
          agent_performance: Json | null;
          final_transaction: Json | null;
          started_at: string;
          completed_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          workflow_id: string;
          user_id: string;
          transaction_id?: string | null;
          workflow_mode?: string;
          status?: string;
          current_stage?: string | null;
          user_input?: string | null;
          input_type?: string | null;
          raw_transaction_count?: number | null;
          duplicates_detected?: number | null;
          duplicates_skipped?: number | null;
          predicted_category?: string | null;
          category_confidence?: number | null;
          category_probabilities?: Json | null;
          transaction_type?: string | null;
          transaction_type_confidence?: number | null;
          merchant_name?: string | null;
          merchant_standardized?: string | null;
          merchant_category?: string | null;
          is_merchant_known?: boolean | null;
          merchant_confidence?: number | null;
          extracted_entities?: Json | null;
          spending_patterns?: Json | null;
          pattern_insights?: Json | null;
          recurring_transactions?: Json | null;
          anomalies_detected?: Json | null;
          pattern_confidence?: number | null;
          budget_recommendations?: Json | null;
          spending_suggestions?: Json | null;
          savings_opportunities?: Json | null;
          suggestion_confidence?: number | null;
          potential_monthly_savings?: number | null;
          security_alerts?: Json | null;
          risk_assessment?: Json | null;
          fraud_score?: number | null;
          anomaly_score?: number | null;
          safety_confidence?: number | null;
          requires_human_review?: boolean | null;
          validation_errors?: Json | null;
          data_quality_score?: number | null;
          is_valid?: boolean | null;
          processing_history?: Json | null;
          confidence_scores?: Json | null;
          error_log?: Json | null;
          retry_count?: number | null;
          total_processing_time?: number | null;
          stage_timings?: Json | null;
          agent_performance?: Json | null;
          final_transaction?: Json | null;
          started_at?: string;
          completed_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          workflow_id?: string;
          user_id?: string;
          transaction_id?: string | null;
          workflow_mode?: string;
          status?: string;
          current_stage?: string | null;
          user_input?: string | null;
          input_type?: string | null;
          raw_transaction_count?: number | null;
          duplicates_detected?: number | null;
          duplicates_skipped?: number | null;
          predicted_category?: string | null;
          category_confidence?: number | null;
          category_probabilities?: Json | null;
          transaction_type?: string | null;
          transaction_type_confidence?: number | null;
          merchant_name?: string | null;
          merchant_standardized?: string | null;
          merchant_category?: string | null;
          is_merchant_known?: boolean | null;
          merchant_confidence?: number | null;
          extracted_entities?: Json | null;
          spending_patterns?: Json | null;
          pattern_insights?: Json | null;
          recurring_transactions?: Json | null;
          anomalies_detected?: Json | null;
          pattern_confidence?: number | null;
          budget_recommendations?: Json | null;
          spending_suggestions?: Json | null;
          savings_opportunities?: Json | null;
          suggestion_confidence?: number | null;
          potential_monthly_savings?: number | null;
          security_alerts?: Json | null;
          risk_assessment?: Json | null;
          fraud_score?: number | null;
          anomaly_score?: number | null;
          safety_confidence?: number | null;
          requires_human_review?: boolean | null;
          validation_errors?: Json | null;
          data_quality_score?: number | null;
          is_valid?: boolean | null;
          processing_history?: Json | null;
          confidence_scores?: Json | null;
          error_log?: Json | null;
          retry_count?: number | null;
          total_processing_time?: number | null;
          stage_timings?: Json | null;
          agent_performance?: Json | null;
          final_transaction?: Json | null;
          started_at?: string;
          completed_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "prediction_results_transaction_id_fkey";
            columns: ["transaction_id"];
            isOneToOne: false;
            referencedRelation: "transactions";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "prediction_results_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
      profiles: {
        Row: {
          created_at: string | null;
          email: string;
          full_name: string | null;
          id: string;
          username: string;
        };
        Insert: {
          created_at?: string | null;
          email: string;
          full_name?: string | null;
          id?: string;
          username: string;
        };
        Update: {
          created_at?: string | null;
          email?: string;
          full_name?: string | null;
          id?: string;
          username?: string;
        };
        Relationships: [];
      };
      transactions: {
        Row: {
          account_type: string | null;
          amount: number;
          category: string | null;
          confidence: number | null;
          created_at: string | null;
          date: string;
          description: string;
          id: string;
          merchant: string | null;
          payment_method: string | null;
          status: string;
          subcategory: string | null;
          transaction_type: string;
          updated_at: string | null;
          user_id: string;
        };
        Insert: {
          account_type?: string | null;
          amount: number;
          category?: string | null;
          confidence?: number | null;
          created_at?: string | null;
          date: string;
          description: string;
          id?: string;
          merchant?: string | null;
          payment_method?: string | null;
          status?: string;
          subcategory?: string | null;
          transaction_type: string;
          updated_at?: string | null;
          user_id: string;
        };
        Update: {
          account_type?: string | null;
          amount?: number;
          category?: string | null;
          confidence?: number | null;
          created_at?: string | null;
          date?: string;
          description?: string;
          id?: string;
          merchant?: string | null;
          payment_method?: string | null;
          status?: string;
          subcategory?: string | null;
          transaction_type?: string;
          updated_at?: string | null;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "transactions_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "profiles";
            referencedColumns: ["id"];
          }
        ];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">;

type DefaultSchema = DatabaseWithoutInternals[Extract<
  keyof Database,
  "public"
>];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
      DefaultSchema["Views"])
  ? (DefaultSchema["Tables"] &
      DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
      Row: infer R;
    }
    ? R
    : never
  : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
  ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
      Insert: infer I;
    }
    ? I
    : never
  : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
  ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
      Update: infer U;
    }
    ? U
    : never
  : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
  ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
  : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
  ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
  : never;

export const Constants = {
  public: {
    Enums: {},
  },
} as const;
