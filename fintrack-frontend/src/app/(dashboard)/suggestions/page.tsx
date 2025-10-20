"use client";

import { useState, useEffect } from "react";
import { useApp } from "@/app/providers";
import { useCurrency } from "@/hooks/useCurrency";
import {
  SparklesIcon,
  ChartBarIcon,
  BanknotesIcon,
  LightBulbIcon,
  ShoppingBagIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
  StarIcon,
} from "@heroicons/react/24/outline";

// Type definitions based on backend models
type SuggestionType = "budget" | "savings" | "spending" | "goal" | "category" | "merchant" | "security";
type SuggestionPriority = "low" | "medium" | "high" | "critical";
type SuggestionStatus = "active" | "implemented" | "dismissed" | "expired";

interface Suggestion {
  id?: string;
  type: SuggestionType;
  title: string;
  description: string;
  priority: SuggestionPriority;
  status: SuggestionStatus;
  potential_savings?: number;
  implementation_difficulty: string;
  category?: string;
  created_at?: string;
  expires_at?: string;
  metadata?: Record<string, unknown>;
}

interface BudgetRecommendation {
  monthly_income: number;
  recommended_budget: Record<string, number>;
  current_spending: Record<string, number>;
  adjustments: Array<{
    category: string;
    current_amount: number;
    recommended_amount: number;
    difference: number;
    type: string;
    priority: string;
  }>;
  savings_potential: number;
  confidence_score: number;
}

interface SpendingSuggestion {
  title: string;
  description: string;
  potential_savings: number;
  potential_monthly_savings?: number;
  category?: string;
  priority?: string;
  implementation_difficulty?: string;
  metadata?: Record<string, unknown>;
}

interface SavingsOpportunity {
  title: string;
  description: string;
  potential_savings: number;
  potential_monthly_savings?: number;
  actionable_tips?: string[];
  category?: string;
  priority?: string;
  metadata?: Record<string, unknown>;
}



export default function SuggestionsPage() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [budgetRecommendations, setBudgetRecommendations] = useState<BudgetRecommendation | null>(null);
  const [spendingSuggestions, setSpendingSuggestions] = useState<SpendingSuggestion[]>([]);
  const [savingsOpportunities, setSavingsOpportunities] = useState<SavingsOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [generatingTips, setGeneratingTips] = useState(false);
  const { auth } = useApp();
  const { formatAmount } = useCurrency();

  // Helper function to replace hardcoded $ in descriptions with proper currency
  const formatDescriptionCurrency = (description: string): string => {
    if (!description) return description;
    
    // Match patterns like $18249.67, $2281.21, $1,234.56 (with or without commas)
    // Changed \d{1,3} to \d+ to match any number of digits (handles $18249.67)
    // \b ensures word boundary to prevent matching across multiple amounts
    const currencyPattern = /\$(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b/g;
    
    let result = description;
    const matches = [...description.matchAll(currencyPattern)];
    
    // Replace in reverse order to maintain correct string indices
    for (let i = matches.length - 1; i >= 0; i--) {
      const match = matches[i];
      const fullMatch = match[0]; // e.g., "$18249.67"
      const amount = match[1]; // e.g., "18249.67"
      const index = match.index!;
      
      // Remove commas and parse the number
      const numericValue = parseFloat(amount.replace(/,/g, ''));
      
      // Format with proper currency (e.g., "Rs. 18,249.67")
      const formatted = formatAmount(numericValue);
      
      // Replace the match in the string
      result = result.substring(0, index) + formatted + result.substring(index + fullMatch.length);
    }
    
    return result;
  };

  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      loadSuggestions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.isAuthenticated, auth.user, selectedFilter]);

  const tryGeneratePersonalizedSuggestions = async () => {
    setGeneratingTips(true);
    setError("");

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/v1/suggestions/personalized?user_id=${auth.user?.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          financial_goals: ['savings', 'budget_optimization'],
          risk_tolerance: 'medium',
          preferences: {
            focus_areas: ['spending_reduction', 'savings_increase']
          }
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.suggestions && data.suggestions.suggestions && data.suggestions.suggestions.length > 0) {
          // Convert personalized suggestions to our format
          const personalizedSuggestions: Suggestion[] = data.suggestions.suggestions.map((sugg: any) => ({
            id: `personalized_${Math.random().toString(36).substr(2, 9)}`,
            type: mapSuggestionType(sugg.suggestion_type || sugg.type),
            title: sugg.title || "Personalized Suggestion",
            description: sugg.description || "",
            priority: sugg.priority as SuggestionPriority || "medium",
            status: "active",
            potential_savings: sugg.potential_savings || 0,
            implementation_difficulty: sugg.implementation_difficulty || "medium",
            category: sugg.category || "general",
            created_at: new Date().toISOString(),
            metadata: sugg.metadata || {}
          }));

          setSuggestions(personalizedSuggestions);
          setError("");
        } else {
          setError("Generated suggestions, but they may not be available yet. Try refreshing the page.");
        }
      } else {
        setError("Unable to generate personalized tips right now. Try uploading some transactions first.");
      }
    } catch (err) {
      console.warn('Failed to generate personalized suggestions:', err);
      setError("Failed to generate AI tips. Please check your connection and try again.");
    } finally {
      setGeneratingTips(false);
    }
  };

  const loadSuggestions = async () => {
    setLoading(true);
    setError("");

    try {
      // Load suggestions from stored prediction results (READ-ONLY, no pipeline trigger)
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/prediction-results/user/${auth.user?.id}/suggestions`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();

        // Convert backend suggestions to frontend format
        const allSuggestions: Suggestion[] = [];

        // Process all suggestions from the response
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data.suggestions.forEach((suggestion: any) => {
          allSuggestions.push({
                        // Use backend-provided ID if available, otherwise generate consistent ID
            id: suggestion.id || `suggestion_${suggestion.workflow_id}_${generateConsistentId(suggestion)}`,
            type: mapSuggestionType(suggestion.suggestion_type),
            title: suggestion.title || suggestion.category || "Financial Suggestion",
            description: suggestion.description || suggestion.message || "",
            priority: suggestion.priority as SuggestionPriority || "medium",
            status: "active",
            potential_savings: suggestion.potential_savings || suggestion.potential_monthly_savings || 0,
            implementation_difficulty: suggestion.implementation_difficulty || suggestion.metadata?.difficulty || "medium",
            category: suggestion.category,
            created_at: suggestion.generated_at || new Date().toISOString(),
            metadata: {
              ...suggestion.metadata,
              workflow_id: suggestion.workflow_id
            }
          });
        });

        setSuggestions(allSuggestions);

        // Set spending suggestions if available
        if (data.spending_suggestions && data.spending_suggestions.length > 0) {
          setSpendingSuggestions(data.spending_suggestions.map((sugg: any) => ({
            title: sugg.title || sugg.name || "Spending Optimization",
            description: sugg.description || "Optimize your spending in this area",
            potential_savings: sugg.potential_savings || 0,
            potential_monthly_savings: sugg.potential_monthly_savings || sugg.potential_savings || 0,
            category: sugg.category || "general",
            priority: sugg.priority || "medium",
            implementation_difficulty: sugg.implementation_difficulty || "medium",
            metadata: sugg.metadata || {}
          })));
        }

        // Set savings opportunities if available
        if (data.savings_opportunities && data.savings_opportunities.length > 0) {
          setSavingsOpportunities(data.savings_opportunities.map((opp: any) => ({
            title: opp.title || opp.name || "Savings Opportunity",
            description: opp.description || "Potential area for savings",
            potential_savings: opp.potential_savings || 0,
            potential_monthly_savings: opp.potential_monthly_savings || opp.potential_savings || 0,
            actionable_tips: opp.tips || opp.action_steps || [],
            category: opp.category || "general",
            priority: opp.priority || "medium",
            metadata: opp.metadata || {}
          })));
        }

        // Set budget recommendations if available
        if (data.budget_recommendations && data.budget_recommendations.length > 0) {
          console.log('Budget recommendations available:', data.budget_recommendations.length);
        }

        // Clear any previous errors if we successfully loaded data
        if (allSuggestions.length > 0 || data.spending_suggestions?.length > 0 || data.savings_opportunities?.length > 0) {
          setError("");
        } else {
          // No suggestions but response was OK - show helpful message
          setError("No suggestions available yet. Upload transactions to get personalized recommendations!");
        }

      } else if (response.status === 404) {
        // No prediction results found for this user - try to generate personalized suggestions
        await tryGeneratePersonalizedSuggestions();
      } else {
        // Other error responses
        setSuggestions([]);
        setSpendingSuggestions([]);
        setSavingsOpportunities([]);
        setError("Unable to load suggestions. Please try again later.");
      }
    } catch (err) {
      console.warn('Failed to load suggestions:', err);
      setSuggestions([]);
      setSpendingSuggestions([]);
      setSavingsOpportunities([]);
      setError("Failed to load suggestions. Please check your connection and try uploading transactions.");
    }

    setLoading(false);
  };

  const generateConsistentId = (suggestion: any): string => {
    // Generate consistent ID based on suggestion content
    const contentFields = [
      suggestion.title || "",
      suggestion.description || "",
      suggestion.category || "",
      suggestion.suggestion_type || "",
      String(suggestion.potential_savings || 0),
      String(suggestion.potential_monthly_savings || 0)
    ];

    const contentString = contentFields.join("|").toLowerCase();

    // Simple hash function for consistency (not for security)
    let hash = 0;
    for (let i = 0; i < contentString.length; i++) {
      const char = contentString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }

    return Math.abs(hash).toString(36);
  };

  const mapSuggestionType = (backendType: string): SuggestionType => {
    const typeMap: Record<string, SuggestionType> = {
      'budget_adjustment': 'budget',
      'budget_optimization': 'budget',
      'budget_review': 'budget',
      'savings_opportunity': 'savings',
      'savings_increase': 'savings',
      'spending_reduction': 'spending',
      'spending_optimization': 'spending',
      'category_optimization': 'category',
      'category_analysis': 'category',
      'merchant_analysis': 'merchant',
      'security_alert': 'security',
      'goal_setting': 'goal',
      'subscription_review': 'spending',
      'spending_analysis': 'category',
      'financial_overview': 'budget'
    };
    return typeMap[backendType] || 'budget';
  };





  const loadBudgetRecommendations = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(
        `${API_BASE}/api/v1/suggestions/budget?user_id=${auth.user?.id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ monthly_income: 5000 }), // TODO: Get from user profile
        }
      );

      if (response.ok) {
        const data = await response.json();
        setBudgetRecommendations(data);
        setShowBudgetModal(true);
      }
    } catch (err) {
      console.error("Failed to load budget recommendations:", err);
      setError("Failed to load budget recommendations. Please try again.");
    }
  };

  const handleFeedback = async (
    suggestionId: string,
    rating: number,
    feedbackType: string
  ) => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/v1/suggestions/feedback?user_id=${auth.user?.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          suggestion_id: suggestionId,
          rating,
          feedback_type: feedbackType,
        }),
      });

      if (response.ok) {
        // Update suggestion status locally
        setSuggestions(prev =>
          prev.map(s =>
            s.id === suggestionId
              ? { ...s, status: feedbackType === "implemented" ? "implemented" : feedbackType === "dismissed" ? "dismissed" : s.status }
              : s
          )
        );

        // Show success message
        if (feedbackType === "implemented") {
          setError("");
          // You could show a success toast here
        }
      } else {
        setError("Failed to submit feedback. Please try again.");
      }
    } catch (err) {
      console.error("Failed to submit feedback:", err);
      setError("Failed to submit feedback. Please check your connection.");
    }
  };

  const getPriorityColor = (priority: SuggestionPriority) => {
    switch (priority) {
      case "critical":
        return "from-red-500 to-pink-500";
      case "high":
        return "from-orange-500 to-red-500";
      case "medium":
        return "from-yellow-500 to-orange-500";
      case "low":
        return "from-blue-500 to-cyan-500";
      default:
        return "from-gray-500 to-slate-500";
    }
  };

  const getPriorityBadgeColor = (priority: SuggestionPriority) => {
    switch (priority) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-300";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getTypeIcon = (type: SuggestionType) => {
    switch (type) {
      case "budget":
        return <ChartBarIcon className="w-6 h-6" />;
      case "savings":
        return <BanknotesIcon className="w-6 h-6" />;
      case "spending":
        return <ShoppingBagIcon className="w-6 h-6" />;
      case "goal":
        return <ArrowTrendingUpIcon className="w-6 h-6" />;
      case "security":
        return <ExclamationTriangleIcon className="w-6 h-6" />;
      default:
        return <LightBulbIcon className="w-6 h-6" />;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "easy":
        return "text-green-600";
      case "medium":
        return "text-yellow-600";
      case "hard":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const totalPotentialSavings = suggestions.reduce(
    (sum, s) => sum + (s.potential_savings || 0),
    0
  );

  const totalSpendingSavings = spendingSuggestions.reduce(
    (sum, s) => sum + (s.potential_monthly_savings || s.potential_savings || 0),
    0
  );

  const totalSavingsOpportunities = savingsOpportunities.reduce(
    (sum, s) => sum + (s.potential_monthly_savings || s.potential_savings || 0),
    0
  );

  const combinedTotalSavings = totalPotentialSavings + totalSpendingSavings + totalSavingsOpportunities;

  const activeSuggestionsCount = suggestions.filter(
    (s) => s.status === "active"
  ).length;

  const implementedCount = suggestions.filter(
    (s) => s.status === "implemented"
  ).length;

  const totalOpportunities = spendingSuggestions.length + savingsOpportunities.length;

  // Extract savings-focused suggestions from main suggestions
  const savingsFocusedSuggestions = suggestions.filter(s =>
    s.type === 'savings' ||
    s.title.toLowerCase().includes('save') ||
    s.title.toLowerCase().includes('reduce') ||
    s.description.toLowerCase().includes('savings') ||
    (s.potential_savings && s.potential_savings > 0)
  );

  // Calculate total potential savings from all sources
  const totalPotentialFromSuggestions = savingsFocusedSuggestions.reduce(
    (sum, s) => sum + (s.potential_savings || 0), 0
  );

  // Filter suggestions based on selected filter
  const filteredSuggestions = suggestions.filter((suggestion) => {
    if (selectedFilter === "all") return true;
    if (selectedFilter === "savings") {
      // For savings filter, show both savings type and suggestions with savings potential
      return suggestion.type === selectedFilter ||
             suggestion.title.toLowerCase().includes('save') ||
             suggestion.title.toLowerCase().includes('reduce') ||
             (suggestion.potential_savings && suggestion.potential_savings > 0);
    }
    return suggestion.type === selectedFilter;
  });

  // Filter spending suggestions based on selected filter
  const filteredSpendingSuggestions = selectedFilter === "all" || selectedFilter === "spending"
    ? spendingSuggestions
    : [];

  // Filter savings opportunities based on selected filter
  const filteredSavingsOpportunities = selectedFilter === "all" || selectedFilter === "savings"
    ? savingsOpportunities
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
          <p className="mt-6 text-lg text-gray-600 font-medium">
            Generating AI-powered suggestions...
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Analyzing your spending patterns
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg">
                  <SparklesIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    AI Suggestions
                  </h1>
                  <p className="text-slate-600 mt-1 text-lg">
                    Personalized financial recommendations powered by AI
                  </p>
                </div>
              </div>
            </div>
            <div className="hidden md:flex space-x-3">
              <button
                onClick={loadSuggestions}
                className="px-6 py-3 bg-white border-2 border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 transition-all font-medium flex items-center space-x-2"
              >
                <ArrowPathIcon className="w-5 h-5" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border-2 border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-center justify-between">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-6 h-6 mr-3" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError("")}
              className="text-red-500 hover:text-red-700"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* AI-Powered Insights Summary */}
        {(suggestions.length > 0 || spendingSuggestions.length > 0 || savingsOpportunities.length > 0) && (
          <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg p-8 text-white">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-white/20 rounded-xl mr-4">
                <SparklesIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Your Financial Optimization Summary</h2>
                <p className="text-purple-100">AI-powered analysis of your spending patterns</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white/10 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-lg font-semibold mb-2">Potential Monthly Savings</h3>
                <div className="text-3xl font-bold mb-2">
                  {formatAmount(combinedTotalSavings > 0 ? combinedTotalSavings : 0)}
                </div>
                <p className="text-sm text-purple-100">
                  From {suggestions.length + spendingSuggestions.length + savingsOpportunities.length} personalized suggestions
                </p>
              </div>

              <div className="bg-white/10 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-lg font-semibold mb-2">Priority Actions</h3>
                <div className="text-3xl font-bold mb-2">
                  {suggestions.filter(s => s.priority === 'high' || s.priority === 'critical').length}
                </div>
                <p className="text-sm text-purple-100">
                  High-impact recommendations ready to implement
                </p>
              </div>

              <div className="bg-white/10 rounded-xl p-6 backdrop-blur-sm">
                <h3 className="text-lg font-semibold mb-2">Categories Analyzed</h3>
                <div className="text-3xl font-bold mb-2">
                  {new Set([
                    ...suggestions.map(s => s.category).filter(Boolean),
                    ...spendingSuggestions.map(s => s.category).filter(Boolean),
                    ...savingsOpportunities.map(s => s.category).filter(Boolean)
                  ]).size}
                </div>
                <p className="text-sm text-purple-100">
                  Spending areas with optimization potential
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Active Suggestions"
            value={activeSuggestionsCount.toString()}
            icon={<LightBulbIcon className="w-6 h-6" />}
            gradient="from-purple-500 to-pink-500"
            description="Pending actions"
          />
          <StatCard
            title="Potential Savings"
            value={formatAmount(combinedTotalSavings)}
            icon={<BanknotesIcon className="w-6 h-6" />}
            gradient="from-green-500 to-emerald-500"
            description="Monthly savings potential"
          />
          <StatCard
            title="Opportunities"
            value={totalOpportunities.toString()}
            icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
            gradient="from-orange-500 to-red-500"
            description="Spending & savings tips"
          />
        </div>

        {/* Filter Tabs */}
        <div className="bg-white rounded-2xl shadow-lg p-2 border border-slate-200">
          <div className="flex items-center space-x-2 overflow-x-auto">
            <FilterTab
              label="Spending"
              active={selectedFilter === "spending"}
              onClick={() => setSelectedFilter("spending")}
            />
            <FilterTab
              label="Savings"
              active={selectedFilter === "savings"}
              onClick={() => setSelectedFilter("savings")}
            />
            <FilterTab
              label="Budget"
              active={selectedFilter === "budget"}
              onClick={() => setSelectedFilter("budget")}
            />
          </div>
        </div>



        {/* Comprehensive Savings Dashboard - Only show when savings filter is active */}
        {selectedFilter === "savings" && (savingsFocusedSuggestions.length > 0 || filteredSavingsOpportunities.length > 0) && (
          <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl shadow-lg p-8 text-white mb-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-white/20 rounded-xl mr-4">
                <BanknotesIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-3xl font-bold">Your Complete Savings Strategy</h2>
                <p className="text-green-100 text-lg">AI-powered recommendations to maximize your financial growth</p>
              </div>
            </div>

            {/* Savings Overview Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white/15 rounded-xl p-4 backdrop-blur-sm">
                <div className="text-sm text-green-100 mb-1">Direct Savings</div>
                <div className="text-2xl font-bold">{formatAmount(totalPotentialFromSuggestions)}</div>
                <div className="text-xs text-green-200">From {savingsFocusedSuggestions.length} suggestions</div>
              </div>
              <div className="bg-white/15 rounded-xl p-4 backdrop-blur-sm">
                <div className="text-sm text-green-100 mb-1">Opportunities</div>
                <div className="text-2xl font-bold">{formatAmount(totalSavingsOpportunities)}</div>
                <div className="text-xs text-green-200">From {filteredSavingsOpportunities.length} opportunities</div>
              </div>
              <div className="bg-white/15 rounded-xl p-4 backdrop-blur-sm">
                <div className="text-sm text-green-100 mb-1">Total Monthly</div>
                <div className="text-2xl font-bold">{formatAmount(totalPotentialFromSuggestions + totalSavingsOpportunities)}</div>
                <div className="text-xs text-green-200">Combined potential</div>
              </div>
              <div className="bg-white/15 rounded-xl p-4 backdrop-blur-sm">
                <div className="text-sm text-green-100 mb-1">Annual Impact</div>
                <div className="text-2xl font-bold">{formatAmount((totalPotentialFromSuggestions + totalSavingsOpportunities) * 12)}</div>
                <div className="text-xs text-green-200">Yearly projection</div>
              </div>
            </div>

            {/* Savings Categories Breakdown */}
            <div className="bg-white/10 rounded-xl p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold mb-4">Savings by Category</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {(() => {
                  const categoryBreakdown: Record<string, { amount: number; count: number }> = {};

                  // Add from suggestions
                  savingsFocusedSuggestions.forEach(s => {
                    const category = s.category || 'general';
                    if (!categoryBreakdown[category]) {
                      categoryBreakdown[category] = { amount: 0, count: 0 };
                    }
                    categoryBreakdown[category].amount += s.potential_savings || 0;
                    categoryBreakdown[category].count += 1;
                  });

                  // Add from opportunities
                  filteredSavingsOpportunities.forEach(opp => {
                    const category = opp.category || 'general';
                    if (!categoryBreakdown[category]) {
                      categoryBreakdown[category] = { amount: 0, count: 0 };
                    }
                    categoryBreakdown[category].amount += opp.potential_monthly_savings || opp.potential_savings || 0;
                    categoryBreakdown[category].count += 1;
                  });

                  return Object.entries(categoryBreakdown)
                    .sort(([,a], [,b]) => b.amount - a.amount)
                    .map(([category, data]) => (
                      <div key={category} className="bg-white/10 rounded-lg p-3">
                        <div className="text-xs text-green-100 font-medium capitalize mb-1">{category}</div>
                        <div className="text-lg font-bold">{formatAmount(data.amount)}</div>
                        <div className="text-xs text-green-200">{data.count} item{data.count > 1 ? 's' : ''}</div>
                      </div>
                    ));
                })()}
              </div>
            </div>
          </div>
        )}

        {/* Main Suggestions Grid - Hidden when savings filter is active */}
        {selectedFilter !== "savings" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredSuggestions.map((suggestion, idx) => (
                <SuggestionCard
                  key={suggestion.id || idx}
                  suggestion={suggestion}
                  onFeedback={handleFeedback}
                  getPriorityColor={getPriorityColor}
                  getPriorityBadgeColor={getPriorityBadgeColor}
                  getTypeIcon={getTypeIcon}
                  getDifficultyColor={getDifficultyColor}
                  formatAmount={formatAmount}
                  formatDescriptionCurrency={formatDescriptionCurrency}
                />
              ))
            }
          </div>
        )}

        {/* Success Stories Section */}
        {implementedCount > 0 && (
          <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl shadow-lg p-8 text-white">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-white/20 rounded-xl mr-4">
                <CheckCircleIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Great Progress!</h2>
                <p className="text-green-100">You&apos;ve implemented {implementedCount} financial improvement{implementedCount > 1 ? 's' : ''}</p>
              </div>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <p className="text-sm text-green-100">
                Keep up the momentum! Each implemented suggestion brings you closer to your financial goals.
                Continue exploring new recommendations to maximize your savings potential.
              </p>
            </div>
          </div>
        )}

        {/* Budget Recommendations Modal */}
        {showBudgetModal && budgetRecommendations && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-slate-200 p-6 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-slate-800">
                  Budget Recommendations
                </h2>
                <button
                  onClick={() => setShowBudgetModal(false)}
                  className="text-slate-500 hover:text-slate-700"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
              <div className="p-6 space-y-6">
                {/* Monthly Income */}
                <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl p-6 text-white">
                  <div className="text-lg font-medium mb-2">
                    Monthly Income
                  </div>
                  <div className="text-4xl font-bold">
                    {formatAmount(budgetRecommendations.monthly_income)}
                  </div>
                  <div className="mt-2 text-green-100">
                    Confidence: {(budgetRecommendations.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>

                {/* Savings Potential */}
                {budgetRecommendations.savings_potential > 0 && (
                  <div className="bg-blue-50 border-2 border-blue-300 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-blue-900 mb-1">
                          Potential Monthly Savings
                        </div>
                        <div className="text-3xl font-bold text-blue-600">
                          {formatAmount(budgetRecommendations.savings_potential)}
                        </div>
                      </div>
                      <BanknotesIcon className="w-12 h-12 text-blue-500" />
                    </div>
                  </div>
                )}

                {/* Budget Breakdown */}
                <div>
                  <h3 className="text-lg font-bold text-slate-800 mb-4">
                    Recommended Budget Allocation
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(budgetRecommendations.recommended_budget).map(
                      ([category, amount]) => {
                        const current =
                          budgetRecommendations.current_spending[category] || 0;
                        const percentage =
                          (amount / budgetRecommendations.monthly_income) * 100;
                        return (
                          <div
                            key={category}
                            className="bg-slate-50 rounded-lg p-4"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-slate-800 capitalize">
                                {category}
                              </span>
                              <span className="text-lg font-bold text-slate-800">
                                {formatAmount(amount)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-600">
                                Current: {formatAmount(current)}
                              </span>
                              <span className="text-slate-500">
                                {percentage.toFixed(1)}% of income
                              </span>
                            </div>
                            <div className="mt-2 h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                                style={{ width: `${Math.min(percentage, 100)}%` }}
                              />
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                </div>

                {/* Adjustments Needed */}
                {budgetRecommendations.adjustments.length > 0 && (
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 mb-4">
                      Recommended Adjustments
                    </h3>
                    <div className="space-y-3">
                      {budgetRecommendations.adjustments.map((adj, idx) => (
                        <div
                          key={idx}
                          className={`border-2 rounded-lg p-4 ${
                            adj.priority === "high"
                              ? "border-red-300 bg-red-50"
                              : "border-yellow-300 bg-yellow-50"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold capitalize">
                              {adj.category}
                            </span>
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-bold ${
                                adj.priority === "high"
                                  ? "bg-red-200 text-red-800"
                                  : "bg-yellow-200 text-yellow-800"
                              }`}
                            >
                              {adj.priority.toUpperCase()}
                            </span>
                          </div>
                          <div className="text-sm space-y-1">
                            <div>
                              Current: {formatAmount(adj.current_amount)}
                            </div>
                            <div>
                              Recommended: {formatAmount(adj.recommended_amount)}
                            </div>
                            <div className="font-semibold text-red-600">
                              Reduce by: {formatAmount(adj.difference)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  gradient,
  description,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  gradient: string;
  description: string;
}) {
  return (
    <div
      className={`bg-gradient-to-br ${gradient} p-6 rounded-2xl shadow-lg text-white relative overflow-hidden`}
    >
      <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-12 -mt-12"></div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="p-2 bg-white/20 rounded-lg">{icon}</div>
        </div>
        <h3 className="text-sm font-medium text-white/80 mb-2">{title}</h3>
        <p className="text-3xl font-bold mb-1">{value}</p>
        <p className="text-sm text-white/70">{description}</p>
      </div>
    </div>
  );
}

function FilterTab({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
        active
          ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg"
          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      }`}
    >
      {label}
    </button>
  );
}

function SuggestionCard({
  suggestion,
  onFeedback,
  getPriorityColor,
  getPriorityBadgeColor,
  getTypeIcon,
  getDifficultyColor,
  formatAmount,
  formatDescriptionCurrency,
}: {
  suggestion: Suggestion;
  onFeedback: (id: string, rating: number, type: string) => void;
  getPriorityColor: (priority: SuggestionPriority) => string;
  getPriorityBadgeColor: (priority: SuggestionPriority) => string;
  getTypeIcon: (type: SuggestionType) => React.ReactNode;
  getDifficultyColor: (difficulty: string) => string;
  formatAmount: (amount: number, includeSymbol?: boolean) => string;
  formatDescriptionCurrency: (description: string) => string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-lg border-2 border-slate-200 overflow-hidden hover:shadow-xl transition-shadow">
      {/* Priority Bar */}
      <div
        className={`h-2 bg-gradient-to-r ${getPriorityColor(
          suggestion.priority
        )}`}
      />

      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3">
            <div
              className={`p-3 bg-gradient-to-br ${getPriorityColor(
                suggestion.priority
              )} rounded-xl text-white`}
            >
              {getTypeIcon(suggestion.type)}
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 mb-1">
                {suggestion.title}
              </h3>
              <div className="flex items-center space-x-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold border ${getPriorityBadgeColor(
                    suggestion.priority
                  )}`}
                >
                  {suggestion.priority.toUpperCase()}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                  {suggestion.type.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-slate-600 mb-4 leading-relaxed">
          {formatDescriptionCurrency(suggestion.description)}
        </p>

        {/* Metadata */}
        <div className="grid grid-cols-1 gap-4 mb-4">
          {/* Potential savings - all suggestions are personalized */}
          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-xs font-medium mb-1 text-green-600">
              {suggestion.potential_savings && suggestion.potential_savings > 0 ? 'Monthly Savings' : 'Impact'}
            </div>
            <div className="text-2xl font-bold text-green-600">
              {suggestion.potential_savings && suggestion.potential_savings > 0
                ? formatAmount(suggestion.potential_savings)
                : 'High'}
            </div>
          </div>
        </div>

        {/* Additional metadata from backend */}
        {suggestion.metadata && Object.keys(suggestion.metadata).length > 0 && (
          <div className="mb-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <div className="text-xs text-slate-600 font-medium mb-2">AI Analysis Details</div>
              <div className="space-y-1">
                {(() => {
                  const metadata = suggestion.metadata as Record<string, any>;
                  const details = [];

                  if (metadata.based_on) {
                    details.push(
                      <div key="based_on" className="text-xs text-slate-700">
                        <span className="font-medium">Analysis:</span> {String(metadata.based_on).replace(/_/g, ' ')}
                      </div>
                    );
                  }

                  if (metadata.current_spending) {
                    details.push(
                      <div key="current_spending" className="text-xs text-slate-700">
                        <span className="font-medium">Current spending:</span> {formatAmount(Number(metadata.current_spending))}
                      </div>
                    );
                  }

                  if (metadata.reduction_percentage) {
                    details.push(
                      <div key="reduction_percentage" className="text-xs text-slate-700">
                        <span className="font-medium">Target reduction:</span> {metadata.reduction_percentage}%
                      </div>
                    );
                  }

                  if (metadata.transaction_count) {
                    details.push(
                      <div key="transaction_count" className="text-xs text-slate-700">
                        <span className="font-medium">Based on:</span> {metadata.transaction_count} transactions
                      </div>
                    );
                  }

                  if (metadata.personalized) {
                    details.push(
                      <div key="personalized" className="text-xs text-green-700">
                        <span className="font-medium">✨ Personalized for you</span>
                      </div>
                    );
                  }

                  return details;
                })()}
              </div>
            </div>
          </div>
        )}

        {/* Category */}
        {suggestion.category && (
          <div className="mb-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {suggestion.category}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
