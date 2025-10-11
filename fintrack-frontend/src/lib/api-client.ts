const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || "v1";

import { ConversationContext } from "./types";

export interface ApiResponse<T = unknown> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
}

export interface Transaction {
  id?: string;
  amount: number;
  description: string;
  date: string;
  merchant?: string;
  category?: string;
  subcategory?: string;
  transaction_type?: "debit" | "credit";
  status?: string;
  payment_method?: string;
  account_type?: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}



export interface ConversationContextRequest {
  previous_transactions?: Transaction[];
  user_preferences?: Record<string, unknown>;
  session_id?: string;
  conversation_history?: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
  }>;
}

class APIClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/${API_VERSION}`;

    // Try to load token from localStorage if available
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.detail || "Request failed");
      }

      return {
        status: "success",
        data,
      };
    } catch (error) {
      console.error("API request failed:", error);
      return {
        status: "error",
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  }

  // Health Check
  async healthCheck() {
    return this.request("/health");
  }

  // Authentication Endpoints
  async login(
    username: string,
    password: string
  ): Promise<ApiResponse<AuthResponse>> {
    const response = await this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });

    if (response.status === "success" && response.data?.access_token) {
      this.setToken(response.data.access_token);
    }

    return response;
  }

  async register(userData: {
    username: string;
    email: string;
    password: string;
    full_name: string;
  }) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async logout() {
    this.clearToken();
    return this.request("/auth/logout", {
      method: "POST",
    });
  }

  async getUserProfile() {
    return this.request<User>("/auth/me");
  }

  // Transaction Endpoints
  async getTransactions(params?: {
    limit?: number;
    offset?: number;
    filters?: Record<string, string | number | boolean>;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());

    return this.request<{ transactions: Transaction[]; total: number }>(
      `/transactions?${queryParams}`
    );
  }

  async createTransaction(transaction: Transaction) {
    return this.request<Transaction>("/transactions", {
      method: "POST",
      body: JSON.stringify(transaction),
    });
  }

  async batchCreateTransactions(transactions: Transaction[]) {
    return this.request("/transactions/batch", {
      method: "POST",
      body: JSON.stringify(transactions),
    });
  }

  async updateTransaction(id: string, transaction: Partial<Transaction>) {
    return this.request<Transaction>(`/transactions/${id}`, {
      method: "PUT",
      body: JSON.stringify(transaction),
    });
  }

  async deleteTransaction(id: string) {
    return this.request(`/transactions/${id}`, {
      method: "DELETE",
    });
  }

  async uploadTransactions(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("file_type", "csv"); // Add file_type parameter

    try {
      const response = await fetch(`${this.baseUrl}/transactions/upload`, {
        method: "POST",
        headers: {
          ...(this.token && { Authorization: `Bearer ${this.token}` }),
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorData}`);
      }

      const data = await response.json();

      return {
        status: "success",
        data: data,
      };
    } catch (error) {
      console.error("Upload transaction error:", error);
      return {
        status: "error",
        error: error instanceof Error ? error.message : "Upload failed",
      };
    }
  }

  // Categorization Endpoints
  async categorizeTransaction(transaction: Partial<Transaction>) {
    return this.request("/categorize", {
      method: "POST",
      body: JSON.stringify(transaction),
    });
  }

  async batchCategorize(transactions: Partial<Transaction>[]) {
    return this.request("/categorize/batch", {
      method: "POST",
      body: JSON.stringify({ transactions }),
    });
  }

  // Analytics Endpoints
  async getSpendingAnalytics(
    period: string = "monthly",
    filters?: Record<string, string | number | boolean>
  ) {
    const queryParams = new URLSearchParams({ period });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        queryParams.append(key, String(value));
      });
    }

    return this.request(`/analytics/spending?${queryParams}`);
  }

  async getCategoryBreakdown(period: string = "monthly") {
    return this.request(`/analytics/categories/${period}`);
  }

  async getTrends(metric: string = "spending", period: string = "daily") {
    return this.request(`/analytics/trends?metric=${metric}&period=${period}`);
  }

  // Suggestions Endpoints
  async getSuggestions(type: string = "all") {
    return this.request(`/suggestions/${type}`);
  }

  async getBudgetRecommendations(
    income: number,
    currentSpending: Record<string, number>
  ) {
    return this.request("/suggestions/budget", {
      method: "POST",
      body: JSON.stringify({ income, current_spending: currentSpending }),
    });
  }

  async getSavingsOpportunities(transactions: Transaction[]) {
    return this.request("/suggestions/savings", {
      method: "POST",
      body: JSON.stringify({ transactions }),
    });
  }

  // Security Endpoints
  async runFraudDetection(transactions: Transaction[]) {
    return this.request("/security/fraud-detection", {
      method: "POST",
      body: JSON.stringify({ transactions }),
    });
  }

  async getSecurityAlerts() {
    return this.request("/security/alerts");
  }

  // Workflow Endpoints
  async getWorkflowModes() {
    return this.request("/workflow/modes");
  }

  async getAgentPerformance() {
    return this.request("/agents/performance");
  }

  // Conversational Transaction Entry
  async processNaturalLanguageTransaction(
    userInput: string,
    conversationContext?: ConversationContext
  ) {
    return this.request("/transactions/natural-language", {
      method: "POST",
      body: JSON.stringify({
        user_input: userInput,
        conversation_context: conversationContext,
      }),
    });
  }
}

// Export singleton instance
export const apiClient = new APIClient();
export default apiClient;
