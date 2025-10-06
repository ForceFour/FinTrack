"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { Transaction } from "@/lib/types";
import AgentStatusWidget from "@/components/AgentStatusWidget";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
];

export default function DashboardPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    setLoading(true);
    const response = await apiClient.getTransactions({ limit: 100 });

    if (response.status === "success" && response.data) {
      setTransactions(response.data.transactions || []);
    } else {
      setError(response.error || "Failed to load transactions");
    }
    setLoading(false);
  };

  // Calculate metrics
  const expenses = transactions.filter(
    (t) => t.transaction_type === "expense" || t.amount < 0
  );
  const income = transactions.filter(
    (t) => t.transaction_type === "income" || t.amount > 0
  );

  const totalExpenses = expenses.reduce(
    (sum, t) => sum + Math.abs(t.amount),
    0
  );
  const totalIncome = income.reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const netCashFlow = totalIncome - totalExpenses;
  const avgTransaction =
    transactions.length > 0 ? totalExpenses / expenses.length : 0;

  // Category breakdown
  const categoryData = expenses.reduce((acc: Record<string, number>, t) => {
    const category = t.category || "Uncategorized";
    acc[category] = (acc[category] || 0) + Math.abs(t.amount);
    return acc;
  }, {});

  const categoryChartData = Object.entries(categoryData).map(
    ([name, value]) => ({
      name,
      value: Number(value.toFixed(2)),
    })
  );

  // Daily spending trend
  const dailyData = expenses.reduce((acc: Record<string, number>, t) => {
    const date = format(new Date(t.date), "MM/dd");
    acc[date] = (acc[date] || 0) + Math.abs(t.amount);
    return acc;
  }, {});

  const trendChartData = Object.entries(dailyData)
    .map(([date, amount]) => ({ date, amount: Number(amount.toFixed(2)) }))
    .slice(-30); // Last 30 days

  // Recent transactions
  const recentTransactions = [...transactions]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 10);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Expense Dashboard</h1>
        <p className="text-gray-600 mt-2">
          AI-Powered Financial Intelligence Overview
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Expenses"
          value={`$${totalExpenses.toFixed(2)}`}
          delta="-12.5%"
          deltaType="negative"
        />
        <MetricCard
          title="Total Income"
          value={`$${totalIncome.toFixed(2)}`}
          delta="+8.3%"
          deltaType="positive"
        />
        <MetricCard
          title="Net Cash Flow"
          value={`$${netCashFlow.toFixed(2)}`}
          delta={`${((netCashFlow / totalIncome) * 100).toFixed(1)}%`}
          deltaType={netCashFlow >= 0 ? "positive" : "negative"}
        />
        <MetricCard
          title="Avg Transaction"
          value={`$${avgTransaction.toFixed(2)}`}
          delta="+5.2%"
          deltaType="positive"
        />
        <MetricCard
          title="Total Transactions"
          value={transactions.length.toString()}
          delta="+23"
          deltaType="positive"
        />
      </div>

      {/* Agent Status */}
      <AgentStatusWidget />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Expenses by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} (${(percent * 100).toFixed(0)}%)`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryChartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Trend */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Daily Spending Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#8884d8"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">🤖 AI-Generated Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InsightCard
            icon="📈"
            title="Spending Trend"
            message={`Your spending increased by 12% compared to last month. Total: $${totalExpenses.toFixed(
              2
            )}`}
            type="warning"
          />
          <InsightCard
            icon="🏪"
            title="Top Category"
            message={`Most spending in '${
              categoryChartData[0]?.name || "N/A"
            }' category ($${categoryChartData[0]?.value.toFixed(2) || 0})`}
            type="info"
          />
          <InsightCard
            icon="💰"
            title="Savings Rate"
            message={`You saved ${((netCashFlow / totalIncome) * 100).toFixed(
              1
            )}% of your income this month`}
            type="success"
          />
          <InsightCard
            icon="⚠️"
            title="Budget Alert"
            message="You've exceeded your dining budget by 15% this month"
            type="error"
          />
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Recent Transactions</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Merchant
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentTransactions.map((transaction, idx) => (
                <tr key={transaction.id || idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(transaction.date), "yyyy-MM-dd")}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.merchant || "Unknown"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.category || "Uncategorized"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <span
                      className={
                        transaction.amount < 0
                          ? "text-red-600"
                          : "text-green-600"
                      }
                    >
                      ${Math.abs(transaction.amount).toFixed(2)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                    {transaction.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  delta,
  deltaType,
}: {
  title: string;
  value: string;
  delta?: string;
  deltaType?: "positive" | "negative";
}) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {delta && (
        <p
          className={`text-sm mt-2 ${
            deltaType === "positive" ? "text-green-600" : "text-red-600"
          }`}
        >
          {delta}
        </p>
      )}
    </div>
  );
}

function InsightCard({
  icon,
  title,
  message,
  type,
}: {
  icon: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
}) {
  const bgColors = {
    info: "bg-blue-50 border-blue-200",
    warning: "bg-yellow-50 border-yellow-200",
    error: "bg-red-50 border-red-200",
    success: "bg-green-50 border-green-200",
  };

  return (
    <div className={`p-4 rounded-lg border ${bgColors[type]}`}>
      <div className="flex items-start">
        <span className="text-2xl mr-3">{icon}</span>
        <div>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-700 mt-1">{message}</p>
        </div>
      </div>
    </div>
  );
}
