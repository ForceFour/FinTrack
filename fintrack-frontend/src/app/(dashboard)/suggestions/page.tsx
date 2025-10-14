"use client";

import { useState, useEffect } from "react";
import { useApp } from "@/app/providers";
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



export default function SuggestionsPage() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [budgetRecommendations, setBudgetRecommendations] = useState<BudgetRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const { auth } = useApp();

  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      loadSuggestions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.isAuthenticated, auth.user, selectedFilter]);

  const loadSuggestions = async () => {
    setLoading(true);
    setError("");

    try {
      // Load backend suggestions
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/analytics/suggestions/${auth.user?.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();

        // Convert backend suggestions to frontend format
        const allSuggestions: Suggestion[] = [];

        // Add budget recommendations
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data.suggestions.forEach((suggestion: any) => {
          allSuggestions.push({
            id: `suggestion_${Math.random().toString(36).substr(2, 9)}`,
            type: mapSuggestionType(suggestion.suggestion_type),
            title: suggestion.title,
            description: suggestion.description,
            priority: suggestion.priority as SuggestionPriority,
            status: "active",
            potential_savings: suggestion.potential_savings,
            implementation_difficulty: suggestion.metadata?.difficulty || "medium",
            category: suggestion.category,
            created_at: new Date().toISOString(),
            metadata: suggestion.metadata
          });
        });

        setSuggestions(allSuggestions);

        // Set other data if available
        if (data.budget_recommendations) {
          setBudgetRecommendations(data.budget_recommendations);
        }

      } else {
        // No suggestions available from backend
        setSuggestions([]);
        console.log('No suggestions available from backend');
      }
    } catch (err) {
      console.warn('Backend suggestions not available:', err);
      setSuggestions([]);
    }

    setLoading(false);
  };

  const mapSuggestionType = (backendType: string): SuggestionType => {
    const typeMap: Record<string, SuggestionType> = {
      'budget_adjustment': 'budget',
      'savings_opportunity': 'savings',
      'spending_reduction': 'spending',
      'category_optimization': 'category',
      'merchant_analysis': 'merchant',
      'security_alert': 'security',
      'goal_setting': 'goal'
    };
    return typeMap[backendType] || 'budget';
  };





  const loadBudgetRecommendations = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/v1/suggestions/budget",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${auth.token}`,
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
    }
  };

  const handleFeedback = async (
    suggestionId: string,
    rating: number,
    feedbackType: string
  ) => {
    try {
      await fetch("http://localhost:8000/api/v1/suggestions/feedback", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${auth.token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          suggestion_id: suggestionId,
          rating,
          feedback_type: feedbackType,
        }),
      });

      // Reload suggestions after feedback
      loadSuggestions();
    } catch (err) {
      console.error("Failed to submit feedback:", err);
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

  const activeSuggestionsCount = suggestions.filter(
    (s) => s.status === "active"
  ).length;

  const implementedCount = suggestions.filter(
    (s) => s.status === "implemented"
  ).length;

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
                onClick={loadBudgetRecommendations}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl hover:shadow-lg transition-all font-medium"
              >
                Get Budget Plan
              </button>
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

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            title="Active Suggestions"
            value={activeSuggestionsCount.toString()}
            icon={<LightBulbIcon className="w-6 h-6" />}
            gradient="from-purple-500 to-pink-500"
            description="Pending actions"
          />
          <StatCard
            title="Potential Savings"
            value={`$${totalPotentialSavings.toFixed(2)}`}
            icon={<BanknotesIcon className="w-6 h-6" />}
            gradient="from-green-500 to-emerald-500"
            description="Monthly savings"
          />
          <StatCard
            title="Implemented"
            value={implementedCount.toString()}
            icon={<CheckCircleIcon className="w-6 h-6" />}
            gradient="from-blue-500 to-cyan-500"
            description="Actions taken"
          />
          <StatCard
            title="Savings Rate"
            value="0"
            icon={<ArrowTrendingUpIcon className="w-6 h-6" />}
            gradient="from-orange-500 to-red-500"
            description="Opportunities found"
          />
        </div>

        {/* Filter Tabs */}
        <div className="bg-white rounded-2xl shadow-lg p-2 border border-slate-200">
          <div className="flex items-center space-x-2 overflow-x-auto">
            <FilterTab
              label="All"
              active={selectedFilter === "all"}
              onClick={() => setSelectedFilter("all")}
            />
            <FilterTab
              label="Budget"
              active={selectedFilter === "budget"}
              onClick={() => setSelectedFilter("budget")}
            />
            <FilterTab
              label="Savings"
              active={selectedFilter === "savings"}
              onClick={() => setSelectedFilter("savings")}
            />
            <FilterTab
              label="Spending"
              active={selectedFilter === "spending"}
              onClick={() => setSelectedFilter("spending")}
            />
            <FilterTab
              label="Goals"
              active={selectedFilter === "goals"}
              onClick={() => setSelectedFilter("goals")}
            />
          </div>
        </div>



        {/* Main Suggestions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {suggestions.length === 0 ? (
            <div className="col-span-2 bg-white rounded-2xl shadow-lg p-12 border border-slate-200 text-center">
              <LightBulbIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">
                No suggestions available
              </h3>
              <p className="text-gray-500">
                Start adding transactions to get personalized recommendations
              </p>
            </div>
          ) : (
            suggestions.map((suggestion, idx) => (
              <SuggestionCard
                key={suggestion.id || idx}
                suggestion={suggestion}
                onFeedback={handleFeedback}
                getPriorityColor={getPriorityColor}
                getPriorityBadgeColor={getPriorityBadgeColor}
                getTypeIcon={getTypeIcon}
                getDifficultyColor={getDifficultyColor}
              />
            ))
          )}
        </div>



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
                    ${budgetRecommendations.monthly_income.toFixed(2)}
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
                          ${budgetRecommendations.savings_potential.toFixed(2)}
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
                                ${amount.toFixed(2)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-slate-600">
                                Current: ${current.toFixed(2)}
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
                              Current: ${adj.current_amount.toFixed(2)}
                            </div>
                            <div>
                              Recommended: ${adj.recommended_amount.toFixed(2)}
                            </div>
                            <div className="font-semibold text-red-600">
                              Reduce by: ${adj.difference.toFixed(2)}
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
}: {
  suggestion: Suggestion;
  onFeedback: (id: string, rating: number, type: string) => void;
  getPriorityColor: (priority: SuggestionPriority) => string;
  getPriorityBadgeColor: (priority: SuggestionPriority) => string;
  getTypeIcon: (type: SuggestionType) => React.ReactNode;
  getDifficultyColor: (difficulty: string) => string;
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
          {suggestion.description}
        </p>

        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {suggestion.potential_savings && suggestion.potential_savings > 0 && (
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-xs text-green-600 font-medium mb-1">
                Potential Savings
              </div>
              <div className="text-2xl font-bold text-green-600">
                ${suggestion.potential_savings.toFixed(2)}
              </div>
            </div>
          )}
          <div className="bg-slate-50 rounded-lg p-3">
            <div className="text-xs text-slate-600 font-medium mb-1">
              Difficulty
            </div>
            <div
              className={`text-lg font-bold ${getDifficultyColor(
                suggestion.implementation_difficulty
              )}`}
            >
              {suggestion.implementation_difficulty}
            </div>
          </div>
        </div>

        {/* Category */}
        {suggestion.category && (
          <div className="mb-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {suggestion.category}
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-200">
          <div className="flex items-center space-x-2">
            <button
              onClick={() =>
                onFeedback(suggestion.id || "", 5, "implemented")
              }
              className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg transition-all text-sm font-medium flex items-center space-x-1"
            >
              <CheckCircleIcon className="w-4 h-4" />
              <span>Implement</span>
            </button>
            <button
              onClick={() =>
                onFeedback(suggestion.id || "", 1, "dismissed")
              }
              className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-all text-sm font-medium flex items-center space-x-1"
            >
              <XMarkIcon className="w-4 h-4" />
              <span>Dismiss</span>
            </button>
          </div>
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                onClick={() =>
                  onFeedback(suggestion.id || "", rating, "helpful")
                }
                className="text-gray-400 hover:text-yellow-500 transition-colors"
              >
                <StarIcon className="w-5 h-5" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
