"use client";

import { useState, useEffect } from "react";
import { useApp } from "@/app/providers";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  EyeIcon,
  CreditCardIcon,
  BanknotesIcon,
  ClockIcon,
  MapPinIcon,
} from "@heroicons/react/24/outline";

interface SecurityAlert {
  id: string;
  alert_type: "amount_anomaly" | "frequency_anomaly" | "location_anomaly" | "time_anomaly" | "limit_exceeded" | "security_setup" | "fraud_awareness";
  severity: "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  timestamp: string;
  amount?: number;
  merchant?: string;
  location?: string;
  risk_score?: number;
  recommended_action?: string;
  transaction_id?: string;
  workflow_id?: string;
  detected_at?: string;
}

interface SecurityMetrics {
  riskScore: number;
  totalAlerts: number;
  resolvedAlerts: number;
  fraudAttempts: number;
  unusualTransactions: number;
  securityScore: number;
}

export default function SecurityPage() {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [currencySymbol, setCurrencySymbol] = useState("LKR");
  const { auth } = useApp();

  useEffect(() => {
    const loadData = async () => {
      if (!auth.isAuthenticated || !auth.user) return;

      setLoading(true);

      try {
        // Load currency preference
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const settingsResponse = await fetch(`${API_BASE}/api/user-settings/${auth.user.id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (settingsResponse.ok) {
          const settingsData = await settingsResponse.json();
          if (settingsData.preferences?.currency_symbol) {
            setCurrencySymbol(settingsData.preferences.currency_symbol);
          }
        }

        // Load security data from backend API (READ-ONLY, no pipeline trigger)
        const response = await fetch(`${API_BASE}/api/prediction-results/user/${auth.user.id}/security`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (response.ok) {
          const data = await response.json();

          if (data.total_alerts === 0) {
            // No alerts - system is secure
            setAlerts([]);
            setMetrics({
              riskScore: 0.5,
              totalAlerts: 0,
              resolvedAlerts: 0,
              fraudAttempts: 0,
              unusualTransactions: 0,
              securityScore: 95,
            });
            setLoading(false);
            return;
          }

          // Convert backend alerts to frontend format
          const securityAlerts: SecurityAlert[] = data.security_alerts.map((alert: SecurityAlert, index: number) => ({
            id: alert.workflow_id ? `alert-${alert.workflow_id}-${index}` : `alert-${index}`,
            alert_type: alert.alert_type || "frequency_anomaly",
            severity: alert.severity || "medium",
            title: alert.title || "Security Alert",
            description: alert.description || "",
            timestamp: alert.detected_at || alert.timestamp || new Date().toISOString(),
            merchant: alert.merchant || undefined,
            amount: alert.amount || undefined,
            risk_score: alert.risk_score || 0.5,
            recommended_action: alert.recommended_action || "Review this alert and take appropriate action.",
            transaction_id: alert.transaction_id || undefined,
          }));

          // Generate security metrics based on real data
          const highRiskCount = data.high_risk_count || 0;

          const securityMetrics: SecurityMetrics = {
            riskScore: highRiskCount > 0 ? Math.min(highRiskCount * 1.5, 10) : 0.5,
            totalAlerts: data.total_alerts,
            resolvedAlerts: 0, // Backend should track this
            fraudAttempts: highRiskCount,
            unusualTransactions: data.total_alerts - highRiskCount,
            securityScore: Math.max(95 - (highRiskCount * 15) - ((data.total_alerts - highRiskCount) * 5), 30),
          };

          console.log(`Loaded ${data.total_alerts} security alerts from ${data.workflows_analyzed} workflows`);

          setAlerts(securityAlerts);
          setMetrics(securityMetrics);
        } else {
          // No data available
          setAlerts([]);
          setMetrics({
            riskScore: 0.5,
            totalAlerts: 0,
            resolvedAlerts: 0,
            fraudAttempts: 0,
            unusualTransactions: 0,
            securityScore: 95,
          });
        }
      } catch (err) {
        console.error('Failed to load security data:', err);
        // Show error state
        setAlerts([]);
        setMetrics({
          riskScore: 0,
          totalAlerts: 0,
          resolvedAlerts: 0,
          fraudAttempts: 0,
          unusualTransactions: 0,
          securityScore: 0,
        });
      }

      setLoading(false);
    };

    loadData();
  }, [auth.isAuthenticated, auth.user]);


  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-red-600 bg-red-50 border-red-200";
      case "medium": return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "low": return "text-blue-600 bg-blue-50 border-blue-200";
      default: return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "amount_anomaly": return <BanknotesIcon className="w-5 h-5" />;
      case "frequency_anomaly": return <ClockIcon className="w-5 h-5" />;
      case "location_anomaly": return <MapPinIcon className="w-5 h-5" />;
      case "time_anomaly": return <ClockIcon className="w-5 h-5" />;
      case "limit_exceeded": return <ExclamationTriangleIcon className="w-5 h-5" />;
      case "security_setup": return <ShieldCheckIcon className="w-5 h-5" />;
      case "fraud_awareness": return <EyeIcon className="w-5 h-5" />;
      default: return <ShieldExclamationIcon className="w-5 h-5" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours} hours ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading security data...</p>
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
              <h1 className="text-4xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
                Security Center
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                AI-Powered Financial Security Monitoring
              </p>
            </div>
            <div className="hidden md:block">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
                metrics && metrics.securityScore >= 80
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white'
                  : 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white'
              }`}>
                <ShieldCheckIcon className="w-5 h-5" />
                <span className="text-sm font-medium">Security Score: {metrics?.securityScore}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-red-500 to-pink-500 p-6 rounded-2xl shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <ShieldExclamationIcon className="w-8 h-8" />
                <div className="w-3 h-3 bg-white/30 rounded-full"></div>
              </div>
              <h3 className="text-sm font-medium text-white/80 mb-2">Risk Score</h3>
              <p className="text-3xl font-bold">{metrics.riskScore}/10</p>
              <p className="text-sm text-white/70 mt-2">
                {metrics.riskScore <= 3 ? "Low Risk" : metrics.riskScore <= 6 ? "Medium Risk" : "High Risk"}
              </p>
            </div>

            <div className="bg-gradient-to-br from-yellow-500 to-orange-500 p-6 rounded-2xl shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <ExclamationTriangleIcon className="w-8 h-8" />
                <div className="w-3 h-3 bg-white/30 rounded-full"></div>
              </div>
              <h3 className="text-sm font-medium text-white/80 mb-2">Active Alerts</h3>
              <p className="text-3xl font-bold">{metrics.totalAlerts - metrics.resolvedAlerts}</p>
              <p className="text-sm text-white/70 mt-2">
                {metrics.resolvedAlerts} resolved
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-violet-500 p-6 rounded-2xl shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <CreditCardIcon className="w-8 h-8" />
                <div className="w-3 h-3 bg-white/30 rounded-full"></div>
              </div>
              <h3 className="text-sm font-medium text-white/80 mb-2">Fraud Attempts</h3>
              <p className="text-3xl font-bold">{metrics.fraudAttempts}</p>
              <p className="text-sm text-white/70 mt-2">
                This month
              </p>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-6 rounded-2xl shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <BanknotesIcon className="w-8 h-8" />
                <div className="w-3 h-3 bg-white/30 rounded-full"></div>
              </div>
              <h3 className="text-sm font-medium text-white/80 mb-2">Unusual Transactions</h3>
              <p className="text-3xl font-bold">{metrics.unusualTransactions}</p>
              <p className="text-sm text-white/70 mt-2">
                Flagged for review
              </p>
            </div>
          </div>
        )}

        {/* Security Alerts */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-slate-800">Recent Security Alerts</h3>
            <div className="flex items-center space-x-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-3 py-1 rounded-full text-sm">
              <div className="w-2 h-2 bg-white rounded-full"></div>
              <span>Live Monitoring</span>
            </div>
          </div>

          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-md ${getSeverityColor(alert.severity)}`}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getTypeIcon(alert.alert_type)}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-800">{alert.title}</h4>
                      <p className="text-sm text-slate-600 mt-1">{alert.description}</p>
                      {alert.recommended_action && (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-xs text-blue-800">
                            <strong>Recommended:</strong> {alert.recommended_action}
                          </p>
                        </div>
                      )}
                      <div className="flex items-center space-x-4 mt-2 text-xs text-slate-500">
                        <span>{formatTimestamp(alert.timestamp)}</span>
                        {alert.amount && (
                          <span>Amount: {currencySymbol} {alert.amount.toLocaleString()}</span>
                        )}
                        {alert.merchant && (
                          <span>Merchant: {alert.merchant}</span>
                        )}
                        {alert.location && (
                          <span>Location: {alert.location}</span>
                        )}
                        {alert.risk_score && (
                          <span>Risk: {(alert.risk_score * 10).toFixed(1)}/10</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    alert.severity === 'high' ? 'bg-red-100 text-red-800' :
                    alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.severity.toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Security Tips */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <h3 className="text-xl font-bold text-slate-800 mb-6">Security Best Practices</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <ShieldCheckIcon className="w-4 h-4 text-white" />
                </div>
                <h4 className="font-semibold text-green-800">Enable Two-Factor Authentication</h4>
              </div>
              <p className="text-sm text-green-700">
                Add an extra layer of security to your account with 2FA verification.
              </p>
            </div>

            <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <EyeIcon className="w-4 h-4 text-white" />
                </div>
                <h4 className="font-semibold text-blue-800">Monitor Transactions Regularly</h4>
              </div>
              <p className="text-sm text-blue-700">
                Review your transactions frequently to spot any unauthorized activity.
              </p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                  <ExclamationTriangleIcon className="w-4 h-4 text-white" />
                </div>
                <h4 className="font-semibold text-yellow-800">Set Up Transaction Alerts</h4>
              </div>
              <p className="text-sm text-yellow-700">
                Get notified immediately for transactions above a certain amount.
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                  <CreditCardIcon className="w-4 h-4 text-white" />
                </div>
                <h4 className="font-semibold text-purple-800">Use Secure Payment Methods</h4>
              </div>
              <p className="text-sm text-purple-700">
                Prefer secure payment methods and avoid sharing card details.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-800">Alert Details</h3>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-slate-800">{selectedAlert.title}</h4>
                <p className="text-sm text-slate-600 mt-1">{selectedAlert.description}</p>
              </div>

              {selectedAlert.amount && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Amount: </span>
                  <span className="text-sm text-gray-900">{currencySymbol} {selectedAlert.amount.toLocaleString()}</span>
                </div>
              )}

              {selectedAlert.merchant && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Merchant: </span>
                  <span className="text-sm text-gray-900">{selectedAlert.merchant}</span>
                </div>
              )}

              {selectedAlert.location && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Location: </span>
                  <span className="text-sm text-gray-900">{selectedAlert.location}</span>
                </div>
              )}

              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Time: </span>
                <span className="text-sm text-gray-900">{formatTimestamp(selectedAlert.timestamp)}</span>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setSelectedAlert(null)}
                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
              >
                Dismiss
              </button>
              <button
                onClick={() => setSelectedAlert(null)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Mark as Resolved
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
