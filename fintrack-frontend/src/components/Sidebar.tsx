"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/app/providers";
import { useDashboardSummary } from "@/lib/hooks/useDashboardSummary";
import { useCurrency } from "@/hooks/useCurrency";
import {
  HomeIcon,
  ArrowUpTrayIcon,
  ChartBarIcon,
  LightBulbIcon,
  ShieldCheckIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  DocumentTextIcon,
  CpuChipIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BanknotesIcon,
} from "@heroicons/react/24/outline";



const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: HomeIcon },
  { name: "Transactions", href: "/transactions", icon: DocumentTextIcon },
  { name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { name: "Agent Workflow", href: "/workflow", icon: CogIcon },
  { name: "Suggestions", href: "/suggestions", icon: LightBulbIcon },
  { name: "Security", href: "/security", icon: ShieldCheckIcon },
  {
    name: "Upload Transactions",
    href: "/upload",
    icon: ArrowUpTrayIcon,
    isUpload: true,
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { auth, logout } = useApp();
  const { summary, loading } = useDashboardSummary();
  const { formatAmountCompact } = useCurrency();

  const formatCurrency = (amount: number) => formatAmountCompact(amount, true);

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(1)}%`;
  };

  return (
    <div className="flex flex-col w-64 bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900 text-white h-screen shadow-2xl border-r border-slate-700">
      <div className="flex items-center justify-center h-20 bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg">
        <div className="flex items-center space-x-3">
          <CpuChipIcon className="w-8 h-8 text-white" />
          <h1 className={"font-sans text-2xl font-bold tracking-wide"}>FinTrack</h1>
        </div>
      </div>

      {/* Analytics Insights */}
      {auth.user && (
        <div className="px-4 py-4 bg-slate-800/50 border-b border-slate-700">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            This Month
          </h3>
          <div className="space-y-3">
            {/* Balance */}
            <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg backdrop-blur-sm hover:bg-slate-700/70 transition-all duration-300 hover:scale-105">
              <div className="flex items-center space-x-2">
                <BanknotesIcon className="w-4 h-4 text-green-400" />
                <span className="text-xs text-slate-300">Balance</span>
              </div>
              <span className="text-sm font-semibold text-green-400">
                {loading
                  ? "..."
                  : formatCurrency(summary?.current_balance || 0)}
              </span>
            </div>

            {/* Spending */}
            <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg backdrop-blur-sm hover:bg-slate-700/70 transition-all duration-300 hover:scale-105">
              <div className="flex items-center space-x-2">
                <CurrencyDollarIcon className="w-4 h-4 text-red-400" />
                <span className="text-xs text-slate-300">Spent</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-red-400">
                  {loading
                    ? "..."
                    : formatCurrency(summary?.current_spending || 0)}
                </span>
                {summary?.spending_change !== undefined && (
                  <div
                    className={`flex items-center ${
                      summary.spending_change >= 0
                        ? "text-red-400"
                        : "text-green-400"
                    }`}
                  >
                    {summary.spending_change >= 0 ? (
                      <ArrowTrendingUpIcon className="w-3 h-3" />
                    ) : (
                      <ArrowTrendingDownIcon className="w-3 h-3" />
                    )}
                    <span className="text-xs ml-1">
                      {formatPercentage(Math.abs(summary.spending_change))}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Transactions */}
            <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg backdrop-blur-sm hover:bg-slate-700/70 transition-all duration-300 hover:scale-105">
              <div className="flex items-center space-x-2">
                <DocumentTextIcon className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-slate-300">Transactions</span>
              </div>
              <span className="text-sm font-semibold text-blue-400">
                {loading ? "..." : summary?.transaction_count || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col flex-1 overflow-y-auto">
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation
            .filter((item) => !item.isUpload)
            .map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white hover:shadow-md"
                  }`}
                >
                  <item.icon
                    className={`w-5 h-5 mr-4 transition-colors duration-300 ${
                      isActive
                        ? "text-white"
                        : "text-slate-400 group-hover:text-blue-400"
                    }`}
                  />
                  <span className="font-semibold">{item.name}</span>
                  {isActive && (
                    <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  )}
                </Link>
              );
            })}
        </nav>

        {/* Upload Transactions - Bottom Section */}
        <div className="px-4 pb-4">
          {navigation
            .filter((item) => item.isUpload)
            .map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-4 py-4 text-sm font-medium rounded-lg transition-all duration-300 ease-in-out transform hover:scale-105 border-2 ${
                    isActive
                      ? "bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg border-green-500"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white hover:shadow-md border-slate-600 hover:border-green-500"
                  }`}
                >
                  <item.icon
                    className={`w-6 h-6 mr-4 transition-colors duration-300 ${
                      isActive
                        ? "text-white"
                        : "text-slate-400 group-hover:text-green-400"
                    }`}
                  />
                  <span className="font-semibold text-base">{item.name}</span>
                  {isActive && (
                    <div className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  )}
                </Link>
              );
            })}
        </div>

        <div className="px-4 py-6 border-t border-slate-700 bg-slate-800/50">
          {auth.user && (
            <Link href="/settings">
              <div className="flex items-center px-4 py-3 mb-4 bg-slate-700/50 rounded-lg backdrop-blur-sm hover:bg-slate-700 transition-colors cursor-pointer group">
                <UserCircleIcon className="w-8 h-8 mr-3 text-blue-400 group-hover:text-blue-300 transition-colors" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate group-hover:text-blue-100 transition-colors">
                    {auth.user.full_name}
                  </p>
                  <p className="text-xs text-slate-400 truncate group-hover:text-slate-300 transition-colors">
                    {auth.user.email}
                  </p>
                </div>
                <CogIcon className="w-5 h-5 text-slate-400 group-hover:text-blue-400 transition-colors" />
              </div>
            </Link>
          )}
          <button
            onClick={logout}
            className="flex items-center w-full px-4 py-3 text-sm font-medium text-slate-300 rounded-lg hover:bg-gradient-to-r hover:from-red-600 hover:to-red-700 hover:text-white transition-all duration-300 ease-in-out transform hover:scale-105 shadow-md"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5 mr-4" />
            <span className="font-semibold">Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
}
