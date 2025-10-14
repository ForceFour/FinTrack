"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getTransactions } from "@/lib/transactions";
import { Transaction } from "@/lib/types";
import { useApp } from "@/app/providers";
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
  const { auth, onTransactionsRefresh } = useApp();

  const loadTransactions = useCallback(async () => {
    if (!auth.user) return;

    setLoading(true);

    // Load transactions
    const response = await getTransactions(auth.user.id, {}, 1, 100);
    if (response.error) {
      setError(response.error);
    } else {
      setTransactions(response.data || []);
    }

    setLoading(false);
  }, [auth.user]);

  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      loadTransactions();
    }
  }, [auth.isAuthenticated, auth.user, loadTransactions]);

  // Listen for transaction refresh events
  useEffect(() => {
    const unsubscribe = onTransactionsRefresh(() => {
      loadTransactions();
    });
    return unsubscribe;
  }, [onTransactionsRefresh, loadTransactions]);

  // Calculate metrics
  const expenses = transactions.filter(
    (t) => t.transaction_type === "expense"
  );
  const income = transactions.filter(
    (t) => t.transaction_type === "income"
  );

  const totalExpenses = expenses.reduce(
    (sum, t) => sum + Math.abs(t.amount),
    0
  );
  const totalIncome = income.reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const netCashFlow = totalIncome - totalExpenses;
  const avgTransaction =
    transactions.length > 0 ? totalExpenses / expenses.length : 0;

  // Calculate additional metrics for deltas
  const expenseRatio = totalIncome > 0 ? (totalExpenses / totalIncome) * 100 : 0;
  const uniqueDays = new Set(transactions.map(t => format(new Date(t.date), "yyyy-MM-dd"))).size;
  const transactionsPerDay = uniqueDays > 0 ? transactions.length / uniqueDays : 0;

  // Calculate benchmarks for income and avg transaction
  const incomePerDay = uniqueDays > 0 ? totalIncome / uniqueDays : 0;
  const avgTransactionCategory = avgTransaction < 25 ? "Low" : avgTransaction < 100 ? "Medium" : "High";

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Expense Dashboard
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                AI-Powered Financial Intelligence Overview
              </p>
            </div>
            <div className="hidden md:block">
              <div className="flex items-center space-x-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-full">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                <span className="text-sm font-medium">AI Active</span>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-center">
            <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center mr-3">
              <span className="text-white text-xs">!</span>
            </div>
            {error}
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <MetricCard
            title="Total Expenses"
            value={`$${totalExpenses.toFixed(2)}`}
            delta={`${expenseRatio.toFixed(1)}% of income`}
            deltaType="neutral"
            icon="💸"
            gradient="from-red-500 to-pink-500"
          />
          <MetricCard
            title="Total Income"
            value={`$${totalIncome.toFixed(2)}`}
            delta={`$${incomePerDay.toFixed(2)} per day`}
            deltaType="neutral"
            icon="💰"
            gradient="from-green-500 to-emerald-500"
          />
          <MetricCard
            title="Net Cash Flow"
            value={`$${netCashFlow.toFixed(2)}`}
            delta={totalIncome > 0 ? `${((netCashFlow / totalIncome) * 100).toFixed(1)}% savings` : "N/A"}
            deltaType={netCashFlow >= 0 ? "positive" : "negative"}
            icon="📈"
            gradient={netCashFlow >= 0 ? "from-blue-500 to-cyan-500" : "from-orange-500 to-red-500"}
          />
          <MetricCard
            title="Avg Transaction"
            value={`$${avgTransaction.toFixed(2)}`}
            delta={`${avgTransactionCategory} spending`}
            deltaType="neutral"
            icon="🧾"
            gradient="from-purple-500 to-violet-500"
          />
          <MetricCard
            title="Total Transactions"
            value={transactions.length.toString()}
            delta={`${transactionsPerDay.toFixed(1)} per day`}
            deltaType="neutral"
            icon="📊"
            gradient="from-indigo-500 to-blue-500"
          />
        </div>

        {/* Agent Status */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <AgentStatusWidget />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          {/* Category Breakdown */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-800">Expenses by Category</h3>
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={categoryChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {categoryChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                      stroke="white"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Amount']}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => <span className="text-sm font-medium">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Daily Trend */}
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-800">Daily Spending Trend</h3>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={trendChartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Amount']}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="amount"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2, fill: 'white' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-slate-800">Recent Transactions</h3>
            <Link href="/transactions" className="text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors">
              View All →
            </Link>
          </div>
          <div className="overflow-hidden rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Merchant
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {recentTransactions.map((transaction, idx) => (
                  <tr key={transaction.id || idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                      {format(new Date(transaction.date), "MMM dd, yyyy")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                      {transaction.merchant || "Unknown"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {transaction.category || "Uncategorized"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                      <span
                        className={
                          transaction.transaction_type === "expense"
                            ? "text-red-600"
                            : "text-green-600"
                        }
                      >
                        {transaction.transaction_type === "expense" ? "-" : "+"}${Math.abs(transaction.amount).toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-900 max-w-xs truncate">
                      {transaction.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
  icon,
  gradient,
}: {
  title: string;
  value: string;
  delta?: string;
  deltaType?: "positive" | "negative" | "neutral";
  icon?: string;
  gradient?: string;
}) {
  return (
    <div className={`bg-gradient-to-br ${gradient || 'from-blue-500 to-purple-500'} p-6 rounded-2xl shadow-lg text-white relative overflow-hidden`}>
      <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10"></div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <span className="text-3xl">{icon || '📊'}</span>
          <div className={`w-3 h-3 rounded-full ${
            deltaType === "positive" ? "bg-green-300" :
            deltaType === "negative" ? "bg-red-300" : "bg-white/50"
          }`}></div>
        </div>
        <h3 className="text-sm font-medium text-white/80 mb-2">{title}</h3>
        <p className="text-3xl font-bold mb-2">{value}</p>
        {delta && (
          <p
            className={`text-sm font-medium ${
              deltaType === "positive"
                ? "text-green-200"
                : deltaType === "negative"
                ? "text-red-200"
                : "text-white/70"
            }`}
          >
            {delta}
          </p>
        )}
      </div>
    </div>
  );
}
