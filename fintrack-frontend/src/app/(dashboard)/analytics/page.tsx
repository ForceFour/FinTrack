"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { getTransactions } from "@/lib/transactions";
import { Transaction } from "@/lib/types";
import { useApp } from "@/app/providers";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Area,
  AreaChart,
} from "recharts";
import { format, subDays, addDays } from "date-fns";
import {
  FunnelIcon,
  ChartBarIcon,
  BanknotesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  ShoppingBagIcon,
  DocumentArrowDownIcon,
  SparklesIcon,
  XMarkIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const COLORS = [
  "#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D",
  "#FFC658", "#FF7C7C", "#8DD1E1", "#D084D0", "#FFAB91", "#A5D6A7"
];

const ANALYSIS_TYPES = [
  { id: "overview", label: "Overview", icon: ChartBarIcon },
  { id: "patterns", label: "Spending Patterns", icon: ArrowTrendingUpIcon },
  { id: "trends", label: "Trend Analysis", icon: ArrowTrendingUpIcon },
  { id: "merchants", label: "Merchant Analysis", icon: ShoppingBagIcon },
  { id: "predictions", label: "Predictive Analytics", icon: ChartBarIcon },
] as const;

type AnalysisType = typeof ANALYSIS_TYPES[number]["id"];

interface AnalyticsData {
  totalIncome: number;
  totalExpenses: number;
  netCashflow: number;
  transactionCount: number;
  avgExpense: number;
  avgIncome: number;
  monthlyData: { month: string; income: number; expenses: number; net: number }[];
  categoryData: { category: string; amount: number; count: number; percentage: number }[];
  dailyData: { date: string; amount: number; ma7: number; ma30: number }[];
  merchantData: { merchant: string; totalSpent: number; avgTransaction: number; count: number; firstVisit: string; lastVisit: string }[];
  weeklyPattern: { day: string; amount: number }[];
  recurringPayments: { merchant: string; amount: number; frequency: string; confidence: number }[];
  anomalies: { date: string; amount: number; category: string; deviation: number }[];
  insights: { type: string; message: string; severity: string }[];
}





export default function AnalyticsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisType>("overview");
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [showAnomalies] = useState(true);
  const [amountRange, setAmountRange] = useState({ min: 0, max: 0 });
  const { auth } = useApp();

  const loadAnalyticsData = useCallback(async () => {
    if (!auth.user) return;

    setLoading(true);
    setError("");

    const loadTransactionsFallback = async () => {
      try {
        // Fallback: Load transactions from database
        const response = await getTransactions(auth.user!.id, {}, 1, 1000);

        if (response.error) {
          setError(response.error);
        } else {
          const txs = response.data || [];
          setTransactions(txs);
          
          // Generate analytics data from transactions for fallback
          const expenseTxs = txs.filter(tx => tx.amount < 0);
          const incomeTxs = txs.filter(tx => tx.amount > 0);

          const totalExpenses = expenseTxs.reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
          const totalIncome = incomeTxs.reduce((sum, tx) => sum + tx.amount, 0);

          // Generate category data
          const categoryMap = new Map<string, { amount: number; count: number }>();
          expenseTxs.forEach(tx => {
            if (tx.category) {
              const existing = categoryMap.get(tx.category) || { amount: 0, count: 0 };
              existing.amount += Math.abs(tx.amount);
              existing.count += 1;
              categoryMap.set(tx.category, existing);
            }
          });

          const categoryData = Array.from(categoryMap.entries())
            .map(([category, data]) => ({
              category,
              amount: data.amount,
              count: data.count,
              percentage: totalExpenses > 0 ? (data.amount / totalExpenses) * 100 : 0
            }))
            .sort((a, b) => b.amount - a.amount);

          console.log('Fallback generated categoryData:', categoryData);

          // Set basic analytics data structure
          setAnalyticsData({
            totalIncome,
            totalExpenses,
            netCashflow: totalIncome - totalExpenses,
            transactionCount: txs.length,
            avgExpense: expenseTxs.length > 0 ? totalExpenses / expenseTxs.length : 0,
            avgIncome: incomeTxs.length > 0 ? totalIncome / incomeTxs.length : 0,
            monthlyData: [],
            categoryData,
            dailyData: [],
            merchantData: [],
            weeklyPattern: [],
            recurringPayments: [],
            anomalies: [],
            insights: []
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics data');
      }
    };

    try {
      // READ FROM STORED PREDICTION RESULTS - NO PIPELINE TRIGGER
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const userId = auth.user.id;

      // Fetch analytics from stored prediction results
      const response = await fetch(`${API_BASE}/api/prediction-results/user/${userId}/analytics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Analytics from prediction results:', result);

        if (result.transactions_analyzed === 0) {
          // No analytics data available, load transactions for display
          await loadTransactionsFallback();
          setError("No analytics data available. Upload transactions to generate analytics insights.");
          setLoading(false);
          return;
        }

        // Extract analytics data from stored prediction results
        const spendingPatterns = result.spending_patterns || {};
        const patternInsights = result.pattern_insights || [];

        // Load transactions for generating time-series data
        let transactionsForAnalysis: Transaction[] = [];
        try {
          const txResp = await getTransactions(auth.user.id, {}, 1, 1000);
          if (!txResp.error) {
            transactionsForAnalysis = txResp.data || [];
            setTransactions(transactionsForAnalysis);
          }
        } catch (e) {
          console.warn('Failed to load transactions for display:', e);
        }

        console.log('Stored Analytics Data:', {
          spendingPatterns,
          patternInsightsCount: patternInsights.length,
          transactionsAnalyzed: result.transactions_analyzed,
          loadedTransactions: transactionsForAnalysis.length
        });

        // Process the stored analytics data
        const categories = spendingPatterns.expense_categories || spendingPatterns.categories || {};
        const incomeCategories = spendingPatterns.income_categories || {};
        const merchants = spendingPatterns.merchants || {};

        // Get totals from spending patterns
        const totalExpenses = spendingPatterns.total_expenses || 0;
        const totalIncome = spendingPatterns.total_income || 0;
        const totalTransactions = spendingPatterns.total_transactions || result.transactions_analyzed || 0;

        const categoryDataArray: { category: string; amount: number; count: number; percentage: number }[] = [];

        // Process expense categories
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        Object.entries(categories).forEach(([category, data]: [string, any]) => {
          const amount = Math.abs(data.total_amount || 0); // Ensure positive for display
          if (amount > 0) { // Only add categories with actual expenses
            categoryDataArray.push({
              category,
              amount,
              count: data.count || 0,
              percentage: 0 // Will calculate after we have total
            });
          }
        });

        console.log('Raw categories data:', categories);
        console.log('Processed categoryDataArray:', categoryDataArray);
        console.log('Total expenses for percentage calc:', totalExpenses);

        // Calculate percentages
        categoryDataArray.forEach(item => {
          item.percentage = totalExpenses > 0 ? (item.amount / Math.abs(totalExpenses)) * 100 : 0;
        });

        // Sort by amount descending
        categoryDataArray.sort((a, b) => b.amount - a.amount);

        // Process merchant data - ONLY EXPENSES (negative amounts)
        const merchantDataArray: { merchant: string; totalSpent: number; avgTransaction: number; count: number; firstVisit: string; lastVisit: string }[] = [];
        
        // Filter transactions to get only expenses and calculate merchant data from actual transactions
        const expenseTransactions = transactionsForAnalysis.filter(tx => tx.amount < 0);
        const merchantMapFromTx = new Map<string, { totalSpent: number; count: number; firstVisit: Date; lastVisit: Date }>();
        
        expenseTransactions.forEach(tx => {
          if (tx.merchant) {
            const amount = Math.abs(tx.amount);
            const txDate = new Date(tx.date);

            const existing = merchantMapFromTx.get(tx.merchant);
            if (existing) {
              existing.totalSpent += amount;
              existing.count += 1;
              if (txDate < existing.firstVisit) existing.firstVisit = txDate;
              if (txDate > existing.lastVisit) existing.lastVisit = txDate;
            } else {
              merchantMapFromTx.set(tx.merchant, {
                totalSpent: amount,
                count: 1,
                firstVisit: txDate,
                lastVisit: txDate
              });
            }
          }
        });

        // Convert to array format
        Array.from(merchantMapFromTx.entries()).forEach(([merchant, data]) => {
          merchantDataArray.push({
            merchant,
            totalSpent: data.totalSpent,
            avgTransaction: data.totalSpent / data.count,
            count: data.count,
            firstVisit: data.firstVisit.toISOString(),
            lastVisit: data.lastVisit.toISOString()
          });
        });

        // Sort merchants by total spent descending
        merchantDataArray.sort((a, b) => b.totalSpent - a.totalSpent);

        // Create insights from pattern_insights
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const insights: { type: string; message: string; severity: string }[] = patternInsights.map((insight: any) => ({
          type: insight.insight_type || insight.type || "info",
          message: insight.message || insight.description || "",
          severity: insight.severity || insight.priority || "medium"
        }));

        // Calculate income category count
        const incomeCategoryCount = Object.keys(incomeCategories).length;

        // Generate monthly data from transactions
        const monthlyMap = new Map<string, { income: number; expenses: number }>();
        transactionsForAnalysis.forEach(tx => {
          const monthKey = format(new Date(tx.date), 'MMM yyyy');
          const existing = monthlyMap.get(monthKey) || { income: 0, expenses: 0 };
          if (tx.amount > 0) {
            existing.income += tx.amount;
          } else {
            existing.expenses += Math.abs(tx.amount);
          }
          monthlyMap.set(monthKey, existing);
        });

        const monthlyData = Array.from(monthlyMap.entries())
          .map(([month, data]) => ({
            month,
            income: data.income,
            expenses: data.expenses,
            net: data.income - data.expenses
          }))
          .sort((a, b) => {
            // Sort by date
            const dateA = new Date(a.month);
            const dateB = new Date(b.month);
            return dateA.getTime() - dateB.getTime();
          });

        // Generate daily data from transactions
        const dailyMap = new Map<string, number>();
        transactionsForAnalysis.forEach(tx => {
          if (tx.amount < 0) { // Only expenses
            const dateKey = format(new Date(tx.date), 'yyyy-MM-dd');
            dailyMap.set(dateKey, (dailyMap.get(dateKey) || 0) + Math.abs(tx.amount));
          }
        });

        const dailyDataRaw = Array.from(dailyMap.entries())
          .map(([date, amount]) => ({ date, amount }))
          .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

        // Calculate moving averages
        const dailyData = dailyDataRaw.map((item, index) => {
          const ma7 = index >= 6 ?
            dailyDataRaw.slice(index - 6, index + 1).reduce((sum, d) => sum + d.amount, 0) / 7 :
            item.amount;
          const ma30 = index >= 29 ?
            dailyDataRaw.slice(index - 29, index + 1).reduce((sum, d) => sum + d.amount, 0) / 30 :
            item.amount;
          return { ...item, ma7, ma30 };
        });

        // Generate weekly pattern from transactions
        const weeklyMap = new Map<string, number>();
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        transactionsForAnalysis.forEach(tx => {
          if (tx.amount < 0) { // Only expenses
            const dayOfWeek = dayNames[new Date(tx.date).getDay()];
            weeklyMap.set(dayOfWeek, (weeklyMap.get(dayOfWeek) || 0) + Math.abs(tx.amount));
          }
        });

        const weeklyPattern = dayNames.map(day => ({
          day,
          amount: weeklyMap.get(day) || 0
        }));

        const analyticsData: AnalyticsData = {
          totalIncome: totalIncome,
          totalExpenses: totalExpenses,
          netCashflow: totalIncome - totalExpenses,
          transactionCount: totalTransactions,
          avgExpense: totalTransactions > 0 ? totalExpenses / totalTransactions : 0,
          avgIncome: incomeCategoryCount > 0 ? totalIncome / incomeCategoryCount : 0,
          monthlyData: monthlyData,
          categoryData: categoryDataArray,
          dailyData: dailyData,
          merchantData: merchantDataArray,
          weeklyPattern: weeklyPattern,
          recurringPayments: [],
          anomalies: [],
          insights
        };

        console.log('Processed Analytics Data:', analyticsData);

        setAnalyticsData(analyticsData);

      } else {
        // Fallback to loading transactions
        await loadTransactionsFallback();
        setError("No analytics data available. Upload transactions to generate analytics.");
      }
    } catch (err) {
      console.warn('Failed to load analytics:', err);
      await loadTransactionsFallback();
      setError("Failed to load analytics. Please try again later.");
    }

    setLoading(false);
  }, [auth.user]);



  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      loadAnalyticsData();
    }
  }, [auth.isAuthenticated, auth.user, loadAnalyticsData]);

  // Client-side filtering of analytics data
  const filteredData = useMemo(() => {
    if (!analyticsData) return null;

    // Filter transactions based on controls
    const filtered = transactions.filter(tx => {
      // Date filter
      if (dateRange.start && dateRange.end) {
        const txDate = new Date(tx.date);
        const startDate = new Date(dateRange.start);
        const endDate = new Date(dateRange.end);
        if (txDate < startDate || txDate > endDate) return false;
      }

      // Amount filter - only apply if user has set values
      const absAmount = Math.abs(tx.amount);
      if (amountRange.min > 0 && absAmount < amountRange.min) return false;
      if (amountRange.max > 0 && absAmount > amountRange.max) return false;

      // Category filter
      if (selectedCategories.length > 0 && !selectedCategories.includes(tx.category || '')) {
        return false;
      }

      return true;
    });

    if (filtered.length === 0) return analyticsData; // No data after filtering

    // Recalculate analytics from filtered transactions
    const expenseTxs = filtered.filter(tx => tx.amount < 0);
    const incomeTxs = filtered.filter(tx => tx.amount > 0);

    const newTotalExpenses = expenseTxs.reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
    const newTotalIncome = incomeTxs.reduce((sum, tx) => sum + tx.amount, 0);

    // Category data
    const categoryMap = new Map<string, { amount: number; count: number }>();
    expenseTxs.forEach(tx => {
      if (tx.category) {
        const existing = categoryMap.get(tx.category) || { amount: 0, count: 0 };
        existing.amount += Math.abs(tx.amount);
        existing.count += 1;
        categoryMap.set(tx.category, existing);
      }
    });

    const newCategoryData = Array.from(categoryMap.entries())
      .map(([category, data]) => ({
        category,
        amount: data.amount,
        count: data.count,
        percentage: newTotalExpenses > 0 ? (data.amount / newTotalExpenses) * 100 : 0
      }))
      .sort((a, b) => b.amount - a.amount);

    // Merchant data
    const merchantMap = new Map<string, { totalSpent: number; count: number; firstVisit: Date; lastVisit: Date }>();
    expenseTxs.forEach(tx => {
      if (tx.merchant) {
        const amount = Math.abs(tx.amount);
        const txDate = new Date(tx.date);

        const existing = merchantMap.get(tx.merchant);
        if (existing) {
          existing.totalSpent += amount;
          existing.count += 1;
          if (txDate < existing.firstVisit) existing.firstVisit = txDate;
          if (txDate > existing.lastVisit) existing.lastVisit = txDate;
        } else {
          merchantMap.set(tx.merchant, {
            totalSpent: amount,
            count: 1,
            firstVisit: txDate,
            lastVisit: txDate
          });
        }
      }
    });

    const newMerchantData = Array.from(merchantMap.entries())
      .map(([merchant, data]) => ({
        merchant,
        totalSpent: data.totalSpent,
        avgTransaction: data.totalSpent / data.count,
        count: data.count,
        firstVisit: data.firstVisit.toISOString(),
        lastVisit: data.lastVisit.toISOString()
      }))
      .sort((a, b) => b.totalSpent - a.totalSpent);

    // Monthly data
    const monthlyMap = new Map<string, { income: number; expenses: number }>();
    filtered.forEach(tx => {
      const monthKey = format(new Date(tx.date), 'MMM yyyy');
      const existing = monthlyMap.get(monthKey) || { income: 0, expenses: 0 };
      if (tx.amount > 0) {
        existing.income += tx.amount;
      } else {
        existing.expenses += Math.abs(tx.amount);
      }
      monthlyMap.set(monthKey, existing);
    });

    const newMonthlyData = Array.from(monthlyMap.entries())
      .map(([month, data]) => ({
        month,
        income: data.income,
        expenses: data.expenses,
        net: data.income - data.expenses
      }))
      .sort((a, b) => new Date(a.month).getTime() - new Date(b.month).getTime());

    // Daily data
    const dailyMap = new Map<string, number>();
    expenseTxs.forEach(tx => {
      const dateKey = format(new Date(tx.date), 'yyyy-MM-dd');
      dailyMap.set(dateKey, (dailyMap.get(dateKey) || 0) + Math.abs(tx.amount));
    });

    const dailyDataRaw = Array.from(dailyMap.entries())
      .map(([date, amount]) => ({ date, amount }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    const newDailyData = dailyDataRaw.map((item, index) => {
      const ma7 = index >= 6 ?
        dailyDataRaw.slice(index - 6, index + 1).reduce((sum, d) => sum + d.amount, 0) / 7 :
        item.amount;
      const ma30 = index >= 29 ?
        dailyDataRaw.slice(index - 29, index + 1).reduce((sum, d) => sum + d.amount, 0) / 30 :
        item.amount;
      return { ...item, ma7, ma30 };
    });

    // Weekly pattern
    const weeklyMap = new Map<string, number>();
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    expenseTxs.forEach(tx => {
      const dayOfWeek = dayNames[new Date(tx.date).getDay()];
      weeklyMap.set(dayOfWeek, (weeklyMap.get(dayOfWeek) || 0) + Math.abs(tx.amount));
    });

    const newWeeklyPattern = dayNames.map(day => ({
      day,
      amount: weeklyMap.get(day) || 0
    }));

    const incomeCategoryCount = incomeTxs.reduce((acc, tx) => {
      if (tx.category && !acc.has(tx.category)) {
        acc.add(tx.category);
      }
      return acc;
    }, new Set()).size;

    return {
      ...analyticsData,
      totalExpenses: newTotalExpenses,
      totalIncome: newTotalIncome,
      netCashflow: newTotalIncome - newTotalExpenses,
      transactionCount: filtered.length,
      avgExpense: filtered.length > 0 ? newTotalExpenses / filtered.length : 0,
      avgIncome: incomeCategoryCount > 0 ? newTotalIncome / incomeCategoryCount : 0,
      categoryData: newCategoryData,
      merchantData: newMerchantData,
      monthlyData: newMonthlyData,
      dailyData: newDailyData,
      weeklyPattern: newWeeklyPattern
    };
  }, [analyticsData, transactions, dateRange, amountRange, selectedCategories]);

  // Use filtered data for display, fallback to original if no filters applied
  const displayData = filteredData || analyticsData;

  // Add safety check for displayData
  if (!displayData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-lg p-12 border border-slate-200 text-center max-w-lg">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
            <ChartBarIcon className="h-10 w-10 text-white" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Loading Analytics...</h3>
          <p className="text-gray-600 mb-6">
            Please wait while we prepare your financial insights.
          </p>
        </div>
      </div>
    );
  }

  // Reset filters function
  const resetFilters = () => {
    setDateRange({ start: '', end: '' });
    setAmountRange({ min: 0, max: 0 });
    setSelectedCategories([]);
  };

  const formatCurrency = (amount: number) => {
    return `LKR ${Math.abs(amount).toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    })}`;
  };

  const formatCurrencyCompact = (amount: number) => {
    const abs = Math.abs(amount);
    if (abs >= 1e9) return `LKR ${(abs/1e9).toFixed(1)}B`;
    if (abs >= 1e6) return `LKR ${(abs/1e6).toFixed(1)}M`;
    if (abs >= 1e3) return `LKR ${(abs/1e3).toFixed(1)}K`;
    if (abs >= 100) return `LKR ${abs.toFixed(0)}`;
    if (abs >= 1) return `LKR ${abs.toFixed(2)}`;
    return `LKR ${abs.toFixed(2)}`;
  };

  // Helper to get lastAutoTable.finalY safely
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getLastTableY = (pdf: any, fallback: number) => {
    return pdf.lastAutoTable && typeof pdf.lastAutoTable.finalY === 'number'
      ? pdf.lastAutoTable.finalY + 20
      : fallback;
  }

  const generatePDFReport = () => {
    if (!analyticsData) return;

    const pdf = new jsPDF();
    const pageWidth = pdf.internal.pageSize.width;

    // Helper function to safely get finalY position
    const getNextYPosition = (defaultY: number = 20) => {
      return getLastTableY(pdf, defaultY);
    };

    // Get analysis type label
    const currentAnalysis = ANALYSIS_TYPES.find(type => type.id === selectedAnalysis);
    const analysisTitle = currentAnalysis?.label || 'Overview';

    // Title
    pdf.setFontSize(20);
    pdf.setTextColor(40);
    pdf.text(`FinTrack ${analysisTitle} Report`, pageWidth / 2, 20, { align: 'center' });

    // Date range and filters
    pdf.setFontSize(12);
    pdf.setTextColor(100);
    pdf.text(`Period: ${dateRange.start} to ${dateRange.end}`, pageWidth / 2, 30, { align: 'center' });
    pdf.text(`Amount Range: LKR ${amountRange.min.toLocaleString()} - LKR ${amountRange.max.toLocaleString()}`, pageWidth / 2, 40, { align: 'center' });

    let yPosition = 60;

    // Analysis-specific content based on selected type
    if (selectedAnalysis === "overview") {
      // Overview Report
      pdf.setFontSize(16);
      pdf.setTextColor(40);
      pdf.text('Financial Overview Summary', 20, yPosition);
      yPosition += 10;

      const summaryData = [
        ['Total Income', formatCurrency(displayData.totalIncome)],
        ['Total Expenses', formatCurrency(displayData.totalExpenses)],
        ['Net Cash Flow', formatCurrency(displayData.netCashflow)],
        ['Total Transactions', displayData.transactionCount.toString()],
        ['Average Expense', formatCurrency(displayData.avgExpense)],
        ['Average Income', formatCurrency(displayData.avgIncome)],
        ['Expense Ratio', `${displayData.totalIncome > 0 ? ((displayData.totalExpenses / displayData.totalIncome) * 100).toFixed(1) : 0}%`],
        ['Savings Rate', `${displayData.totalIncome > 0 ? ((displayData.netCashflow / displayData.totalIncome) * 100).toFixed(1) : 0}%`]
      ];

      autoTable(pdf, {
        startY: yPosition,
        head: [['Metric', 'Value']],
        body: summaryData,
        theme: 'striped',
        headStyles: { fillColor: [31, 119, 180] },
      });

      yPosition = getNextYPosition(yPosition + 10);

      // Top Categories
      if (yPosition > 200) {
        pdf.addPage();
        yPosition = 20;
      }

      pdf.setFontSize(14);
      pdf.text('Top Spending Categories', 20, yPosition);
      yPosition += 10;

      const categoryTableData = displayData.categoryData
        .slice(0, 5)
        .map(cat => [
          cat.category,
          formatCurrency(cat.amount),
          `${cat.percentage.toFixed(1)}%`,
          cat.count.toString()
        ]);

      autoTable(pdf, {
        startY: yPosition,
        head: [['Category', 'Amount', 'Percentage', 'Transactions']],
        body: categoryTableData,
        theme: 'striped',
        headStyles: { fillColor: [76, 175, 80] },
      });

     } else if (selectedAnalysis === "patterns") {
       // Spending Patterns Report - Enhanced with proper titles and sections
       pdf.setFontSize(18);
       pdf.setTextColor(40);
       pdf.text('Spending Pattern Analysis', 20, yPosition);
       yPosition += 15;

       // Weekly pattern analysis
       const highestDay = displayData.weeklyPattern.reduce((prev, current) =>
         (prev.amount > current.amount) ? prev : current);
       const lowestDay = displayData.weeklyPattern.reduce((prev, current) =>
         (prev.amount < current.amount) ? prev : current);

       const weekendSpending = displayData.weeklyPattern
         .filter(d => d.day === 'Saturday' || d.day === 'Sunday')
         .reduce((sum, d) => sum + d.amount, 0);
       const weekdaySpending = displayData.weeklyPattern
         .filter(d => !['Saturday', 'Sunday'].includes(d.day))
         .reduce((sum, d) => sum + d.amount, 0);

       // Pattern Summary Section
       pdf.setFontSize(16);
       pdf.setTextColor(40);
       pdf.text('Pattern Summary', 20, yPosition);
       yPosition += 10;

       const patternData = [
         ['Total Transactions Analyzed', displayData.transactionCount.toString()],
         ['Highest Spending Day', `${highestDay.day} (${formatCurrency(highestDay.amount)})`],
         ['Lowest Spending Day', `${lowestDay.day} (${formatCurrency(lowestDay.amount)})`],
         ['Top Spending Category', displayData.categoryData[0]?.category || 'N/A'],
         ['Top Category Amount', formatCurrency(displayData.categoryData[0]?.amount || 0)],
         ['Weekend vs Weekday Ratio', `${weekdaySpending > 0 ? ((weekendSpending / weekdaySpending) * 100).toFixed(1) : 0}%`],
         ['Average Daily Spending', formatCurrency(displayData.totalExpenses / 7)],
         ['Most Active Day', `${highestDay.day} with ${Math.round(displayData.transactionCount / 7)} transactions`]
       ];

       autoTable(pdf, {
         startY: yPosition,
         head: [['Metric', 'Value']],
         body: patternData,
         theme: 'striped',
         headStyles: { fillColor: [52, 168, 83], textColor: [255, 255, 255], fontSize: 12 },
         bodyStyles: { fontSize: 10 },
         columnStyles: { 0: { cellWidth: 80 }, 1: { cellWidth: 80 } },
       });

       yPosition = getNextYPosition(yPosition + 10);

       // Daily Spending Breakdown Section
       if (yPosition > 220) {
         pdf.addPage();
         yPosition = 20;
       }

       pdf.setFontSize(16);
       pdf.setTextColor(40);
       pdf.text('Daily Spending Breakdown', 20, yPosition);
       yPosition += 10;

       const dowData = displayData.weeklyPattern.map(day => {
         const dayTransactions = Math.round(displayData.transactionCount / 7); // Simplified calculation
         const avgPerTransaction = day.amount / dayTransactions || 0;
         return [
           day.day,
           formatCurrency(day.amount),
           `${((day.amount / displayData.totalExpenses) * 100).toFixed(1)}%`,
           formatCurrency(avgPerTransaction)
         ];
       });

       autoTable(pdf, {
         startY: yPosition,
         head: [['Day', 'Total Spending', 'Percentage', 'Avg per Transaction']],
         body: dowData,
         theme: 'striped',
         headStyles: { fillColor: [52, 152, 219], textColor: [255, 255, 255], fontSize: 11 },
         bodyStyles: { fontSize: 9 },
         columnStyles: {
           0: { cellWidth: 40 },
           1: { cellWidth: 45 },
           2: { cellWidth: 35 },
           3: { cellWidth: 45 }
         },
       });

       yPosition = getNextYPosition(yPosition + 15);

       // Category Pattern Analysis Section
       if (yPosition > 200) {
         pdf.addPage();
         yPosition = 20;
       }

       pdf.setFontSize(16);
       pdf.setTextColor(40);
       pdf.text('Top Categories by Spending', 20, yPosition);
       yPosition += 10;

       const topCategoriesData = displayData.categoryData.slice(0, 5).map((cat, index) => [
         (index + 1).toString(),
         cat.category,
         formatCurrency(cat.amount),
         `${cat.percentage.toFixed(1)}%`,
         cat.count.toString()
       ]);

       autoTable(pdf, {
         startY: yPosition,
         head: [['Rank', 'Category', 'Total Amount', 'Percentage', 'Transactions']],
         body: topCategoriesData,
         theme: 'striped',
         headStyles: { fillColor: [155, 89, 182], textColor: [255, 255, 255], fontSize: 11 },
         bodyStyles: { fontSize: 9 },
         columnStyles: {
           0: { cellWidth: 20 },
           1: { cellWidth: 50 },
           2: { cellWidth: 40 },
           3: { cellWidth: 30 },
           4: { cellWidth: 25 }
         },
       });

       yPosition = getNextYPosition(yPosition + 15);

       // Pattern Insights Section
       if (yPosition > 220) {
         pdf.addPage();
         yPosition = 20;
       }

       pdf.setFontSize(16);
       pdf.setTextColor(40);
       pdf.text('Behavioral Insights', 20, yPosition);
       yPosition += 10;

       // Generate insights based on patterns
       const behaviorInsights = [];

       if (weekendSpending > weekdaySpending) {
         behaviorInsights.push(['Weekend Spender', 'You tend to spend more on weekends', 'Consider weekend budgeting']);
       } else {
         behaviorInsights.push(['Weekday Spender', 'Most spending occurs during weekdays', 'Good weekend discipline']);
       }

       const topCategoryPercentage = displayData.categoryData[0]?.percentage || 0;
       if (topCategoryPercentage > 40) {
         behaviorInsights.push(['Category Concentration', `${topCategoryPercentage.toFixed(0)}% spent on ${displayData.categoryData[0]?.category}`, 'Consider diversifying expenses']);
       }

       if (highestDay.amount > (displayData.totalExpenses / 7) * 2) {
         behaviorInsights.push(['Spike Day Pattern', `${highestDay.day} shows unusually high spending`, 'Monitor this day for overspending']);
       }

       if (behaviorInsights.length > 0) {
         autoTable(pdf, {
           startY: yPosition,
           head: [['Pattern Type', 'Observation', 'Recommendation']],
           body: behaviorInsights,
           theme: 'striped',
           headStyles: { fillColor: [241, 196, 15], textColor: [0, 0, 0], fontSize: 11 },
           bodyStyles: { fontSize: 9 },
           columnStyles: {
             0: { cellWidth: 45 },
             1: { cellWidth: 60 },
             2: { cellWidth: 60 }
           },
         });
       }
    } else if (selectedAnalysis === "trends") {
      // Trend Analysis Report
      pdf.setFontSize(16);
      pdf.setTextColor(40);
      pdf.text('Financial Trend Analysis', 20, yPosition);
      yPosition += 10;

      // Calculate trend metrics
      const dailyAmounts = displayData.dailyData.map(d => d.amount);
      const trendDirection = dailyAmounts.length > 1 ?
        (dailyAmounts[dailyAmounts.length - 1] > dailyAmounts[0] ? 'Increasing' : 'Decreasing') : 'Stable';
      const avgDaily = dailyAmounts.reduce((sum, amt) => sum + amt, 0) / dailyAmounts.length;
      const volatility = dailyAmounts.length > 1 ?
        Math.sqrt(dailyAmounts.reduce((sum, amt) => sum + Math.pow(amt - avgDaily, 2), 0) / dailyAmounts.length) / avgDaily * 100 : 0;

      const trendsData = [
        ['Overall Trend Direction', trendDirection],
        ['Average Daily Spending', formatCurrency(avgDaily)],
        ['Spending Volatility', `${volatility.toFixed(1)}%`],
        ['Analysis Period (Days)', displayData.dailyData.length.toString()],
        ['Highest Daily Spending', formatCurrency(Math.max(...dailyAmounts))],
        ['Lowest Daily Spending', formatCurrency(Math.min(...dailyAmounts))],
        ['7-Day Moving Average (Latest)', formatCurrency(displayData.dailyData[displayData.dailyData.length - 1]?.ma7 || 0)]
      ];

      autoTable(pdf, {
        startY: yPosition,
        head: [['Metric', 'Value']],
        body: trendsData,
        theme: 'striped',
        headStyles: { fillColor: [255, 193, 7] },
      });

    } else if (selectedAnalysis === "merchants") {
      // Merchant Analysis Report
      pdf.setFontSize(16);
      pdf.setTextColor(40);
      pdf.text('Merchant Spending Analysis', 20, yPosition);
      yPosition += 10;

      const topMerchant = displayData.merchantData[0];
      const merchantCount = displayData.merchantData.length;
      const avgMerchantSpending = displayData.merchantData.reduce((sum, m) => sum + m.totalSpent, 0) / merchantCount;

      const merchantSummaryData = [
        ['Total Unique Merchants', merchantCount.toString()],
        ['Top Spending Merchant', topMerchant?.merchant || 'N/A'],
        ['Top Merchant Amount', formatCurrency(topMerchant?.totalSpent || 0)],
        ['Average per Merchant', formatCurrency(avgMerchantSpending)],
        ['Merchant Diversity Index', `${merchantCount} unique merchants`]
      ];

      autoTable(pdf, {
        startY: yPosition,
        head: [['Metric', 'Value']],
        body: merchantSummaryData,
        theme: 'striped',
        headStyles: { fillColor: [233, 30, 99] },
      });

      yPosition = getNextYPosition(yPosition + 10);

      // Top 10 merchants table
      if (yPosition > 200) {
        pdf.addPage();
        yPosition = 20;
      }

      pdf.setFontSize(14);
      pdf.text('Top 10 Merchants Detail', 20, yPosition);
      yPosition += 10;

      const topMerchantsData = displayData.merchantData
        .slice(0, 10)
        .map((merchant, index) => [
          (index + 1).toString(),
          merchant.merchant.length > 20 ? merchant.merchant.substring(0, 20) + '...' : merchant.merchant,
          formatCurrency(merchant.totalSpent),
          formatCurrency(merchant.avgTransaction),
          merchant.count.toString()
        ]);

      autoTable(pdf, {
        startY: yPosition,
        head: [['Rank', 'Merchant', 'Total Spent', 'Avg Transaction', 'Visits']],
        body: topMerchantsData,
        theme: 'striped',
        headStyles: { fillColor: [231, 76, 60] },
        columnStyles: {
          0: { cellWidth: 12 },
          1: { cellWidth: 45 },
          2: { cellWidth: 30 },
          3: { cellWidth: 30 },
          4: { cellWidth: 18 }
        }
      });

    } else if (selectedAnalysis === "predictions") {
      // Predictive Analytics Report
      pdf.setFontSize(16);
      pdf.setTextColor(40);
      pdf.text('Predictive Financial Analysis', 20, yPosition);
      yPosition += 10;

      // Calculate forecast data
      const recentDays = displayData.dailyData.slice(-30);
      const recentTrend = recentDays.reduce((sum, d) => sum + d.amount, 0) / recentDays.length;
      const historicalAvg = displayData.dailyData.reduce((sum, d) => sum + d.amount, 0) / displayData.dailyData.length;
      const trendChange = historicalAvg > 0 ? ((recentTrend - historicalAvg) / historicalAvg * 100) : 0;

      const forecast30Days = recentTrend * 30;
      // Calculate confidence based on data points: 30+ days = 75%, 60+ days = 85%, 90+ days = 95%
      const dataPoints = displayData.dailyData.length;
      const baseConfidence = Math.min(0.95, 0.50 + (dataPoints / 90) * 0.45);
      const confidence = Math.round(baseConfidence * 100) / 100; // Round to 2 decimals

      const predictiveData = [
        ['Historical Daily Average', formatCurrency(historicalAvg)],
        ['Recent Trend (30 days)', `${formatCurrency(recentTrend)}/day`],
        ['Trend Direction', trendChange > 0 ? 'Increasing' : trendChange < 0 ? 'Decreasing' : 'Stable'],
        ['30-Day Forecast', formatCurrency(forecast30Days)],
        ['Predicted Monthly Change', `${trendChange > 0 ? '+' : ''}${trendChange.toFixed(1)}%`],
        ['Forecast Confidence', `${(confidence * 100).toFixed(0)}%`],
        ['Data Points Used', `${displayData.dailyData.length} days`]
      ];

      autoTable(pdf, {
        startY: yPosition,
        head: [['Metric', 'Value']],
        body: predictiveData,
        theme: 'striped',
        headStyles: { fillColor: [156, 39, 176] },
      });
    }

    // Footer
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const pageCount = (pdf as any).internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(10);
      pdf.setTextColor(150);
      pdf.text(
        `Generated by FinTrack Analytics System | ${new Date().toLocaleDateString()} | Page ${i} of ${pageCount}`,
        pageWidth / 2,
        pdf.internal.pageSize.height - 10,
        { align: 'center' }
      );
      pdf.text(
        `Report ID: ${new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_')}`,
        pageWidth / 2,
        pdf.internal.pageSize.height - 5,
        { align: 'center' }
      );
    }

    // Save the PDF with analysis-specific filename
    const fileName = `fintrack-${selectedAnalysis}-report-${dateRange.start}-to-${dateRange.end}.pdf`;
    pdf.save(fileName);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto" />
          <p className="mt-4 text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-lg p-12 border border-slate-200 text-center max-w-lg">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center">
            <ChartBarIcon className="h-10 w-10 text-white" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Analytics Dashboard</h3>
          <p className="text-gray-600 mb-6">
            Advanced financial insights and AI-powered analytics are coming soon.
            Add some transactions to see your personalized analytics.
          </p>
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <SparklesIcon className="w-5 h-5" />
            <span className="text-sm font-medium">Powered by AI Intelligence</span>
          </div>
        </div>
      </div>
    );
  }



  // Check if we have no filtered transactions to show empty state
  if (!loading && (!analyticsData || (transactions.length > 0 && !analyticsData))) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
            <div className="text-center py-12">
              <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Transactions Found</h3>
              <p className="text-gray-600 mb-6">
                No transactions match your current filters or date range. Try adjusting your filters or add some transactions to see analytics.
              </p>
              <button
                onClick={() => {
                  // Reset filters
                  setSelectedCategories([]);
                  setAmountRange({ min: 0, max: 0 });
                  setDateRange({
                    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
                    end: format(new Date(), 'yyyy-MM-dd')
                  });
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                Reset Filters
              </button>
            </div>
          </div>
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
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl shadow-lg">
                  <ChartBarIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    Advanced Analytics
                  </h1>
                  <p className="text-slate-600 mt-1 text-lg">AI-Powered Financial Intelligence & Insights</p>
                </div>
              </div>
            </div>
            <div className="hidden md:flex space-x-3">
              <button
                onClick={generatePDFReport}
                className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl hover:shadow-lg transition-all font-medium flex items-center space-x-2"
              >
                <DocumentArrowDownIcon className="w-5 h-5" />
                <span>Export PDF</span>
              </button>
              <div className="px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-xl shadow-md flex items-center space-x-2">
                <SparklesIcon className="w-5 h-5" />
                <span className="font-medium">AI Analytics</span>
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <FunnelIcon className="h-6 w-6 mr-2 text-blue-600" />
              Analytics Controls
            </h2>
            <button
              onClick={resetFilters}
              className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl font-medium text-sm transition-all flex items-center space-x-2"
            >
              <XMarkIcon className="h-5 w-5" />
              <span>Clear Filters</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="w-full px-4 py-2 border-2 border-slate-300 rounded-xl text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                />
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="w-full px-4 py-2 border-2 border-slate-300 rounded-xl text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                />
              </div>
            </div>

            {/* Amount Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Amount Range</label>
              <div className="space-y-2">
                <input
                  type="number"
                  placeholder="Min Amount (optional)"
                  value={amountRange.min || ''}
                  onChange={(e) => setAmountRange(prev => ({ ...prev, min: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-2 border-2 border-slate-300 rounded-xl text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  step="10"
                />
                <input
                  type="number"
                  placeholder="Max Amount (optional)"
                  value={amountRange.max || ''}
                  onChange={(e) => setAmountRange(prev => ({ ...prev, max: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-2 border-2 border-slate-300 rounded-xl text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                  step="10"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Type Tabs */}
        <div className="bg-white rounded-2xl shadow-lg p-2 border border-slate-200">
          <div className="flex items-center space-x-2 overflow-x-auto">
            {ANALYSIS_TYPES.map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  onClick={() => setSelectedAnalysis(type.id)}
                  className={`${
                    selectedAnalysis === type.id
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md'
                      : 'text-gray-600 hover:bg-slate-100'
                  } px-4 py-2.5 rounded-xl font-medium text-sm flex items-center space-x-2 whitespace-nowrap transition-all`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{type.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content based on selected analysis */}
        {selectedAnalysis === "overview" && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Expenses</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrencyCompact(displayData.totalExpenses)}</p>
                    <p className="text-xs text-gray-500 mt-1">{displayData.transactionCount} transactions</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-red-500 to-pink-500 rounded-xl">
                    <ArrowTrendingDownIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Income</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">{formatCurrencyCompact(displayData.totalIncome)}</p>
                    <p className="text-xs text-gray-500 mt-1">Revenue streams</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl">
                    <ArrowTrendingUpIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Net Cash Flow</p>
                    <p className={`text-2xl font-bold mt-1 ${displayData.netCashflow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrencyCompact(displayData.netCashflow)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {displayData.totalIncome > 0 ?
                        `${((displayData.netCashflow / displayData.totalIncome) * 100).toFixed(1)}%` :
                        '0%'
                      } savings rate
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl">
                    <BanknotesIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Expense</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrencyCompact(displayData.avgExpense)}</p>
                    <p className="text-xs text-gray-500 mt-1">Per transaction</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                    <ChartBarIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-md border-2 border-slate-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Income</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrencyCompact(displayData.avgIncome)}</p>
                    <p className="text-xs text-gray-500 mt-1">Per transaction</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                    <ArrowTrendingUpIcon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </div>
            </div>

            {/* AI Insights Section */}
            {displayData.insights && displayData.insights.length > 0 && (
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl shadow-lg border-2 border-purple-200 p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl">
                    <LightBulbIcon className="h-7 w-7 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                      AI-Powered Insights
                    </h3>
                    <p className="text-sm text-slate-600">Smart financial patterns detected by our AI</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {displayData.insights.map((insight, index) => {
                    // Map severity to colors
                    const severityColors = {
                      high: 'from-red-500 to-pink-500',
                      medium: 'from-orange-500 to-yellow-500',
                      low: 'from-green-500 to-emerald-500'
                    };

                    const severityBadges = {
                      high: 'bg-red-100 text-red-700 border-red-300',
                      medium: 'bg-orange-100 text-orange-700 border-orange-300',
                      low: 'bg-green-100 text-green-700 border-green-300'
                    };

                    const gradient = severityColors[insight.severity as keyof typeof severityColors] || severityColors.medium;
                    const badgeStyle = severityBadges[insight.severity as keyof typeof severityBadges] || severityBadges.medium;

                    return (
                      <div key={index} className="bg-white rounded-xl shadow-md border-2 border-slate-200 overflow-hidden hover:shadow-lg transition-shadow">
                        <div className={`h-2 bg-gradient-to-r ${gradient}`} />
                        <div className="p-5">
                          <div className="flex items-start justify-between mb-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${badgeStyle}`}>
                              {insight.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${badgeStyle}`}>
                              {insight.severity.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-slate-700 leading-relaxed">
                            {insight.message}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}



            {/* Income vs Expenses Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Transaction Types (Count)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Income', value: transactions.filter(tx => tx.amount > 0).length, fill: '#10B981' },
                        { name: 'Expenses', value: transactions.filter(tx => tx.amount < 0).length, fill: '#EF4444' }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell fill="#10B981" />
                      <Cell fill="#EF4444" />
                    </Pie>
                    <Tooltip formatter={(value) => [value, 'Transactions']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Transaction Types (Amount)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Income', value: displayData.totalIncome, fill: '#10B981' },
                        { name: 'Expenses', value: displayData.totalExpenses, fill: '#EF4444' }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell fill="#10B981" />
                      <Cell fill="#EF4444" />
                    </Pie>
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Income vs Expenses</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={[
                    { type: 'Income', amount: displayData.totalIncome },
                    { type: 'Expenses', amount: displayData.totalExpenses }
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                    <Bar dataKey="amount" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Monthly Flow */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Financial Flow</h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={displayData.monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis tickFormatter={formatCurrencyCompact} />
                  <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                  <Legend />
                  <Bar dataKey="income" fill="#10B981" name="Income" />
                  <Bar dataKey="expenses" fill="#EF4444" name="Expenses" />
                  <Line type="monotone" dataKey="net" stroke="#3B82F6" strokeWidth={3} name="Net Flow" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {selectedAnalysis === "patterns" && (
          <div className="space-y-8">
            {/* Day of Week & Category Heatmap */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending by Day of Week</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={displayData.weeklyPattern}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                    <Bar dataKey="amount" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Expense Distribution by Category</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={displayData.categoryData.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="category" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                      tick={{ fontSize: 14 }}
                    />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                    <Bar dataKey="amount" fill="#8B5CF6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Transaction Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={displayData.categoryData.slice(0, 6)}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="amount"
                      label={({ category, percentage }) => `${category}: ${percentage.toFixed(1)}%`}
                    >
                      {displayData.categoryData.slice(0, 6).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Categories</h3>
                <div className="space-y-4">
                  {displayData.categoryData.slice(0, 5).map((category, index) => (
                    <div key={category.category} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div
                          className="w-4 h-4 rounded-full mr-3"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span className="font-medium">{category.category}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{formatCurrency(category.amount)}</div>
                        <div className="text-sm text-gray-500">{category.percentage.toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedAnalysis === "trends" && (
          <div className="space-y-8">
            {/* Daily Spending Trends */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Spending Trends with Moving Averages</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={displayData.dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM dd')} />
                  <YAxis tickFormatter={formatCurrencyCompact} />
                  <Tooltip
                    labelFormatter={(date) => format(new Date(date), 'PPP')}
                    formatter={(value, name) => [formatCurrency(Number(value)), name]}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="amount" stroke="#94A3B8" strokeWidth={1} name="Daily Spending" />
                  <Line type="monotone" dataKey="ma7" stroke="#F59E0B" strokeWidth={2} name="7-Day Average" />
                  <Line type="monotone" dataKey="ma30" stroke="#EF4444" strokeWidth={3} name="30-Day Average" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Seasonal Patterns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Spending Pattern</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={displayData.monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Expenses']} />
                    <Line type="monotone" dataKey="expenses" stroke="#10B981" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Spending Pattern</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={displayData.weeklyPattern}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Amount']} />
                    <Bar dataKey="amount" fill="#8B5CF6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {selectedAnalysis === "merchants" && (
          <div className="space-y-8">
            {/* Top Merchants */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Merchants by Spending</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={displayData.merchantData.slice(0, 8)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="merchant" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis tickFormatter={formatCurrencyCompact} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Total Spent']} />
                    <Bar dataKey="totalSpent" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Merchant Analysis: Frequency vs Spending</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart 
                    data={displayData.merchantData}
                    margin={{ top: 20, right: 80, bottom: 60, left: 50 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="count" 
                      name="Transaction Count"
                      type="number"
                      domain={['dataMin - 1', 'dataMax + 1']}
                      tickCount={10}
                      allowDecimals={false}
                      label={{ 
                        value: 'Number of Transactions', 
                        position: 'insideBottom', 
                        offset: -10,
                        style: { textAnchor: 'middle' }
                      }}
                    />
                    <YAxis 
                      dataKey="totalSpent" 
                      name="Total Spent" 
                      type="number"
                      tickFormatter={formatCurrencyCompact}
                      label={{ 
                        value: 'Total Amount Spent', 
                        angle: -90, 
                        position: 'insideLeft',
                        offset: 1000,
                        style: { textAnchor: 'middle' }
                      }}
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                              <div className="font-semibold text-gray-900 mb-2">
                                {data.merchant}
                              </div>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between gap-4">
                                  <span className="text-gray-600">Transactions:</span>
                                  <span className="font-medium">{data.count}</span>
                                </div>
                                <div className="flex justify-between gap-4">
                                  <span className="text-gray-600">Total Spent:</span>
                                  <span className="font-medium">{formatCurrency(data.totalSpent)}</span>
                                </div>
                                <div className="flex justify-between gap-4">
                                  <span className="text-gray-600">Avg per Transaction:</span>
                                  <span className="font-medium">{formatCurrency(data.avgTransaction)}</span>
                                </div>
                                {data.firstVisit && (
                                  <div className="flex justify-between gap-4">
                                    <span className="text-gray-600">First Visit:</span>
                                    <span className="font-medium">{new Date(data.firstVisit).toLocaleDateString()}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    {displayData.merchantData.map((merchant, index) => (
                      <Scatter 
                        key={merchant.merchant}
                        data={[{
                          count: merchant.count,
                          totalSpent: merchant.totalSpent,
                          merchant: merchant.merchant,
                          avgTransaction: merchant.avgTransaction,
                          firstVisit: merchant.firstVisit
                        }]}
                        fill={COLORS[index % COLORS.length]} 
                        shape="circle"
                        r={7}
                      />
                    ))}
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Merchant Details Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Merchant Details</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Merchant
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total Spent
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Transaction
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Transaction Count
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        First Visit
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Visit
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {displayData.merchantData.map((merchant, index) => (
                      <tr key={merchant.merchant} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {merchant.merchant}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(merchant.totalSpent)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(merchant.avgTransaction)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {merchant.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {merchant.firstVisit ? new Date(merchant.firstVisit).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {merchant.lastVisit ? new Date(merchant.lastVisit).toLocaleDateString() : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {selectedAnalysis === "predictions" && (
          <div className="space-y-8">
            {/* Forecast */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">30-Day Spending Forecast</h3>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(displayData.dailyData.slice(-30).reduce((sum, d) => sum + d.amount, 0))}
                  </div>
                  <div className="text-sm text-gray-600">Recent Monthly Spending</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {displayData.dailyData.length > 7 ?
                      `${((displayData.dailyData.slice(-7).reduce((sum, d) => sum + d.amount, 0) /
                          Math.max(1, displayData.dailyData.slice(-14, -7).reduce((sum, d) => sum + d.amount, 0)) - 1) * 100).toFixed(1)}%`
                      : '0%'}
                  </div>
                  <div className="text-sm text-gray-600">Weekly Change</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {(() => {
                      // Calculate confidence based on data points (more data = higher confidence)
                      // Use displayData to respect filters
                      const dataPoints = displayData.dailyData.length;
                      // 30+ days = 75%, 60+ days = 85%, 90+ days = 95%
                      const baseConfidence = Math.min(95, 50 + (dataPoints / 90) * 45);
                      return Math.round(baseConfidence);
                    })()}%
                  </div>
                  <div className="text-sm text-gray-600">Data Confidence</div>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={[
                  // Only show last 30 days of actual data (from 30 days ago to today)
                  ...displayData.dailyData.filter(d => {
                    const dataDate = new Date(d.date);
                    const thirtyDaysAgo = subDays(new Date(), 30);
                    const today = new Date();
                    return dataDate >= thirtyDaysAgo && dataDate <= today;
                  }),
                  // Future predictions (next 30 days)
                  ...Array.from({ length: 30 }, (_, i) => ({
                    date: format(addDays(new Date(), i + 1), 'yyyy-MM-dd'),
                    amount: displayData.dailyData.slice(-1)[0]?.amount * (1 + Math.random() * 0.2 - 0.1) || 0,
                    ma7: 0,
                    ma30: 0,
                    predicted: true
                  }))
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(date) => format(new Date(date), 'MMM dd')} />
                  <YAxis tickFormatter={formatCurrencyCompact} />
                  <Tooltip
                    labelFormatter={(date) => format(new Date(date), 'PPP')}
                    formatter={(value, name) => [formatCurrency(Number(value)), name === 'amount' ? 'Predicted Spending' : name]}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="amount"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                    name="Predicted Spending"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Anomaly Detection */}
        {showAnomalies && analyticsData.anomalies.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
              Anomaly Detection
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deviation</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analyticsData.anomalies.map((anomaly, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {format(new Date(anomaly.date), 'PPP')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{anomaly.category}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-600">
                        {formatCurrency(anomaly.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          anomaly.deviation > 3 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {anomaly.deviation.toFixed(1)}σ
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Export PDF Button */}
        <div className="mt-8 text-center">
          <button
            onClick={generatePDFReport}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
          >
            <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
            Export Analytics Report as PDF
          </button>
        </div>
      </div>
    </div>
  );
}




