"use client";

import { useState, useEffect } from "react";
import { useApp } from "@/app/providers";
import {
  UserCircleIcon,
  CogIcon,
  BellIcon,
  ShieldCheckIcon,
  BanknotesIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";

interface SpendingLimit {
  id: string;
  category: string;
  limit: number;
  period: "monthly" | "weekly";
}

export default function SettingsPage() {
  const { auth } = useApp();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  // User profile state
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");

  // Spending limits state
  const [spendingLimits, setSpendingLimits] = useState<SpendingLimit[]>([]);
  const [newLimit, setNewLimit] = useState({
    category: "food",
    limit: "",
    period: "monthly" as "monthly" | "weekly",
  });

  // User preferences state
  const [currency, setCurrency] = useState("LKR");
  const [currencySymbol, setCurrencySymbol] = useState("LKR");

  const categories = [
    "food",
    "gas",
    "groceries",
    "shopping",
    "entertainment",
    "utilities",
    "healthcare",
    "transportation",
    "education",
    "other",
  ];

  useEffect(() => {
    const loadUserSettings = async () => {
      if (!auth.user) return;

      setLoading(true);
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
        const response = await fetch(`${API_BASE}/api/user-settings/${auth.user.id}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.spending_limits) {
            const limits: SpendingLimit[] = Object.entries(data.spending_limits).map(
              ([category, limit]) => ({
                id: `${category}-${Date.now()}`,
                category,
                limit: limit as number,
                period: "monthly",
              })
            );
            setSpendingLimits(limits);
          }
          // Load currency preference (default to LKR)
          if (data.preferences?.currency) {
            setCurrency(data.preferences.currency);
            setCurrencySymbol(data.preferences.currency_symbol || data.preferences.currency);
          }
        }
      } catch (err) {
        console.error("Failed to load settings:", err);
      }
      setLoading(false);
    };

    if (auth.user) {
      setFullName(auth.user.full_name || "");
      setEmail(auth.user.email || "");
      loadUserSettings();
    }
  }, [auth.user]);

  const saveSettings = async () => {
    if (!auth.user) return;

    setSaving(true);
    setSuccessMessage("");

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

      // Convert spending limits to backend format
      const spending_limits: Record<string, number> = {};
      spendingLimits.forEach((limit) => {
        spending_limits[limit.category] = limit.limit;
      });

      const response = await fetch(`${API_BASE}/api/user-settings/${auth.user.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          spending_limits,
          notifications: {
            email_alerts: true,
            push_notifications: true,
          },
          preferences: {
            currency,
            currency_symbol: currencySymbol,
          },
        }),
      });

      if (response.ok) {
        setSuccessMessage("Settings saved successfully!");
        setTimeout(() => setSuccessMessage(""), 3000);
      } else {
        console.error("Failed to save settings");
      }
    } catch (err) {
      console.error("Failed to save settings:", err);
    }

    setSaving(false);
  };

  const addSpendingLimit = () => {
    if (!newLimit.limit || parseFloat(newLimit.limit) <= 0) {
      return;
    }

    const limit: SpendingLimit = {
      id: `${newLimit.category}-${Date.now()}`,
      category: newLimit.category,
      limit: parseFloat(newLimit.limit),
      period: newLimit.period,
    };

    setSpendingLimits([...spendingLimits, limit]);
    setNewLimit({ category: "food", limit: "", period: "monthly" });
  };

  const removeSpendingLimit = (id: string) => {
    setSpendingLimits(spendingLimits.filter((limit) => limit.id !== id));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Settings
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                Manage your account preferences and spending limits
              </p>
            </div>
            <CogIcon className="w-12 h-12 text-blue-600" />
          </div>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center space-x-3">
            <CheckCircleIcon className="w-6 h-6 text-green-600" />
            <p className="text-green-800 font-medium">{successMessage}</p>
          </div>
        )}

        {/* User Profile Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center space-x-3 mb-6">
            <UserCircleIcon className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-slate-800">User Profile</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your full name"
                disabled
              />
              <p className="text-xs text-slate-500 mt-1">
                Contact support to update your name
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your email"
                disabled
              />
              <p className="text-xs text-slate-500 mt-1">
                Contact support to update your email
              </p>
            </div>
          </div>

          {/* Currency Preference */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Currency Preference
            </label>
            <select
              value={currency}
              onChange={(e) => {
                setCurrency(e.target.value);
                setCurrencySymbol(e.target.value);
              }}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="LKR">Sri Lankan Rupee (LKR)</option>
              <option value="USD">US Dollar (USD)</option>
              <option value="EUR">Euro (EUR)</option>
              <option value="GBP">British Pound (GBP)</option>
              <option value="INR">Indian Rupee (INR)</option>
            </select>
            <p className="text-xs text-slate-500 mt-1">
              This will be used to display amounts throughout the application
            </p>
          </div>
        </div>

        {/* Spending Limits Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center space-x-3 mb-6">
            <BanknotesIcon className="w-6 h-6 text-green-600" />
            <h2 className="text-2xl font-bold text-slate-800">Spending Limits</h2>
          </div>

          <p className="text-slate-600 mb-6">
            Set spending limits for different categories. The Safety Guard will alert you when
            you exceed these limits.
          </p>

          {/* Existing Limits */}
          <div className="space-y-3 mb-6">
            {spendingLimits.length === 0 ? (
              <div className="text-center py-8 bg-slate-50 rounded-lg">
                <BanknotesIcon className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                <p className="text-slate-600">No spending limits set yet</p>
                <p className="text-sm text-slate-500">Add your first limit below</p>
              </div>
            ) : (
              spendingLimits.map((limit) => (
                <div
                  key={limit.id}
                  className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl"
                >
                  <div className="flex-1">
                    <p className="font-semibold text-slate-800 capitalize">
                      {limit.category}
                    </p>
                    <p className="text-sm text-slate-600">
                      {currencySymbol} {limit.limit.toLocaleString()} / {limit.period}
                    </p>
                  </div>
                  <button
                    onClick={() => removeSpendingLimit(limit.id)}
                    className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              ))
            )}
          </div>

          {/* Add New Limit */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
            <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
              <PlusIcon className="w-5 h-5 text-blue-600" />
              <span>Add New Spending Limit</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Category
                </label>
                <select
                  value={newLimit.category}
                  onChange={(e) => setNewLimit({ ...newLimit, category: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Limit Amount ({currencySymbol})
                </label>
                <input
                  type="number"
                  value={newLimit.limit}
                  onChange={(e) => setNewLimit({ ...newLimit, limit: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="10000"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Period
                </label>
                <select
                  value={newLimit.period}
                  onChange={(e) =>
                    setNewLimit({
                      ...newLimit,
                      period: e.target.value as "monthly" | "weekly",
                    })
                  }
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="monthly">Monthly</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
            </div>

            <button
              onClick={addSpendingLimit}
              className="mt-4 w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all"
            >
              <PlusIcon className="w-5 h-5" />
              <span>Add Limit</span>
            </button>
          </div>
        </div>

        {/* Notification Preferences */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center space-x-3 mb-6">
            <BellIcon className="w-6 h-6 text-yellow-600" />
            <h2 className="text-2xl font-bold text-slate-800">Notifications</h2>
          </div>

          <div className="space-y-4">
            <label className="flex items-center space-x-3 p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div>
                <p className="font-medium text-slate-800">Email Alerts</p>
                <p className="text-sm text-slate-600">
                  Receive email notifications for security alerts and limit exceeded
                </p>
              </div>
            </label>

            <label className="flex items-center space-x-3 p-4 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div>
                <p className="font-medium text-slate-800">Push Notifications</p>
                <p className="text-sm text-slate-600">
                  Get instant notifications for important alerts
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center space-x-3 mb-6">
            <ShieldCheckIcon className="w-6 h-6 text-purple-600" />
            <h2 className="text-2xl font-bold text-slate-800">Security</h2>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="font-medium text-slate-800 mb-2">Two-Factor Authentication</p>
              <p className="text-sm text-slate-600 mb-3">
                Add an extra layer of security to your account
              </p>
              <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm">
                Enable 2FA
              </button>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="font-medium text-slate-800 mb-2">Change Password</p>
              <p className="text-sm text-slate-600 mb-3">
                Update your password regularly for better security
              </p>
              <button className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors text-sm">
                Change Password
              </button>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={saveSettings}
            disabled={saving}
            className="px-8 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}
