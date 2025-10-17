import { useState, useEffect } from "react";
import { apiClient } from "../api-client";
import { useApp } from "../../app/providers";

export interface DashboardSummary {
  current_balance: number;
  current_spending: number;
  current_income: number;
  previous_spending: number;
  spending_change: number;
  transaction_count: number;
  top_categories: Array<{
    category: string;
    amount: number;
    percentage: number;
  }>;
  period_start: string;
  period_end: string;
}

export function useDashboardSummary() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { auth } = useApp();

  useEffect(() => {
    const fetchSummary = async () => {
      if (!auth.user?.id) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await apiClient.getDashboardSummary(auth.user.id);

        if (response.status === "success" && response.data) {
          setSummary(response.data as DashboardSummary);
          setError(null);
        } else {
          setError(response.error || "Failed to fetch dashboard summary");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [auth.user?.id]);

  return {
    summary,
    loading,
    error,
    refetch: () => {
      if (auth.user?.id) {
        apiClient.getDashboardSummary(auth.user.id).then((response) => {
          if (response.status === "success" && response.data) {
            setSummary(response.data as DashboardSummary);
            setError(null);
          }
        });
      }
    },
  };
}
