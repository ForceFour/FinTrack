/**
 * Prediction Results Display Component
 * Displays the complete output from the agentic pipeline
 */

"use client";

import { useEffect, useState } from "react";
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  LightBulbIcon,
  ChartBarIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import type { PredictionResult } from "@/lib/types/prediction-results";
import PredictionResultsService from "@/lib/services/prediction-results.service";

interface PredictionResultsDisplayProps {
  workflowId: string;
  onClose?: () => void;
}

export default function PredictionResultsDisplay({
  workflowId,
  onClose,
}: PredictionResultsDisplayProps) {
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPrediction = async () => {
    try {
      setLoading(true);
      const result = await PredictionResultsService.getByWorkflowId(workflowId);
      setPrediction(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load prediction"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrediction();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || "Prediction not found"}</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-blue-100 text-blue-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatConfidence = (confidence?: number | null) => {
    if (!confidence) return "N/A";
    return `${(confidence * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Prediction Results
          </h2>
          <div className="flex items-center space-x-2">
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                prediction.status
              )}`}
            >
              {prediction.status}
            </span>
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircleIcon className="h-6 w-6" />
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Workflow ID</p>
            <p className="text-sm font-mono text-gray-900">
              {prediction.workflow_id}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Mode</p>
            <p className="text-sm font-medium text-gray-900">
              {prediction.workflow_mode}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Processing Time</p>
            <p className="text-sm font-medium text-gray-900">
              {prediction.total_processing_time?.toFixed(2)}s
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Current Stage</p>
            <p className="text-sm font-medium text-gray-900">
              {prediction.current_stage?.replace("_", " ")}
            </p>
          </div>
        </div>
      </div>

      {/* Classification Results */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <ChartBarIcon className="h-6 w-6 text-blue-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">
            Classification
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Predicted Category</p>
            <p className="text-xl font-bold text-gray-900 capitalize">
              {prediction.predicted_category || "Unknown"}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Confidence: {formatConfidence(prediction.category_confidence)}
            </p>
          </div>

          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Transaction Type</p>
            <p className="text-xl font-bold text-gray-900 capitalize">
              {prediction.transaction_type || "Unknown"}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Confidence:{" "}
              {formatConfidence(prediction.transaction_type_confidence)}
            </p>
          </div>
        </div>

        {/* Category Probabilities */}
        {prediction.category_probabilities && (
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700 mb-2">
              Category Probabilities
            </p>
            <div className="space-y-2">
              {Object.entries(prediction.category_probabilities)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 5)
                .map(([category, probability]) => (
                  <div key={category} className="flex items-center">
                    <span className="text-sm text-gray-600 w-32 capitalize">
                      {category.replace("_", " ")}
                    </span>
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-blue-600 h-4 rounded-full"
                        style={{ width: `${(probability as number) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-700 ml-2 w-16 text-right">
                      {formatConfidence(probability as number)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Merchant Information */}
      {prediction.merchant_name && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Merchant Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Merchant Name</p>
              <p className="text-base font-medium text-gray-900">
                {prediction.merchant_name}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Standardized</p>
              <p className="text-base font-medium text-gray-900">
                {prediction.merchant_standardized}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Category</p>
              <p className="text-base font-medium text-gray-900">
                {prediction.merchant_category}
              </p>
            </div>
          </div>
          <div className="mt-2 flex items-center">
            {prediction.is_merchant_known ? (
              <CheckCircleIcon className="h-5 w-5 text-green-600 mr-1" />
            ) : (
              <XCircleIcon className="h-5 w-5 text-gray-400 mr-1" />
            )}
            <span className="text-sm text-gray-600">
              {prediction.is_merchant_known
                ? "Known merchant"
                : "Unknown merchant"}
            </span>
            <span className="text-sm text-gray-500 ml-4">
              Confidence: {formatConfidence(prediction.merchant_confidence)}
            </span>
          </div>
        </div>
      )}

      {/* Pattern Insights */}
      {prediction.pattern_insights &&
        prediction.pattern_insights.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <ChartBarIcon className="h-6 w-6 text-purple-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">
                Pattern Insights
              </h3>
            </div>
            <div className="space-y-3">
              {prediction.pattern_insights.map((insight, idx) => (
                <div
                  key={idx}
                  className={`border-l-4 p-4 rounded-r-lg ${
                    insight.severity === "high"
                      ? "border-red-500 bg-red-50"
                      : insight.severity === "medium"
                      ? "border-yellow-500 bg-yellow-50"
                      : "border-blue-500 bg-blue-50"
                  }`}
                >
                  <p className="font-medium text-gray-900">
                    {insight.description}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Type: {insight.insight_type} • Severity: {insight.severity}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Suggestions */}
      {prediction.spending_suggestions &&
        prediction.spending_suggestions.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <LightBulbIcon className="h-6 w-6 text-yellow-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">
                Suggestions
              </h3>
            </div>
            <div className="space-y-3">
              {prediction.spending_suggestions.map((suggestion, idx) => (
                <div
                  key={idx}
                  className="border rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900">
                        {suggestion.title}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {suggestion.description}
                      </p>
                      {suggestion.potential_savings && (
                        <p className="text-sm font-medium text-green-600 mt-2">
                          Potential savings: Rs.{" "}
                          {suggestion.potential_savings.toFixed(2)}
                        </p>
                      )}
                    </div>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        suggestion.priority === "high"
                          ? "bg-red-100 text-red-800"
                          : suggestion.priority === "medium"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {suggestion.priority}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Security Alerts */}
      {prediction.security_alerts && prediction.security_alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <ShieldExclamationIcon className="h-6 w-6 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Security Alerts
            </h3>
          </div>
          <div className="space-y-3">
            {prediction.security_alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`border-l-4 p-4 rounded-r-lg ${
                  alert.severity === "critical"
                    ? "border-red-600 bg-red-50"
                    : alert.severity === "high"
                    ? "border-orange-500 bg-orange-50"
                    : alert.severity === "medium"
                    ? "border-yellow-500 bg-yellow-50"
                    : "border-blue-500 bg-blue-50"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{alert.title}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {alert.description}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Risk Score: {formatConfidence(alert.risk_score)}
                    </p>
                    <p className="text-sm font-medium text-gray-700 mt-1">
                      {alert.recommended_action}
                    </p>
                  </div>
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing History */}
      {prediction.processing_history &&
        prediction.processing_history.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <ClockIcon className="h-6 w-6 text-gray-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">
                Processing Timeline
              </h3>
            </div>
            <div className="relative">
              {prediction.processing_history.map((entry, idx) => (
                <div key={idx} className="flex items-start mb-4 last:mb-0">
                  <div className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-600 mt-2"></div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {entry.stage.replace("_", " ")}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </p>
                    {entry.message && (
                      <p className="text-sm text-gray-600 mt-1">
                        {entry.message}
                      </p>
                    )}
                    {entry.confidence && (
                      <p className="text-xs text-gray-500 mt-1">
                        Confidence: {formatConfidence(entry.confidence)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  );
}
