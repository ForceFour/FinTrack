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
  const [amountRange, setAmountRange] = useState({ min: 0, max: 100000 });
  const { auth } = useApp();

  // Calculate max amount from transactions
  const maxAmount = useMemo(() => {
    if (transactions.length === 0) return 100000;
    return Math.max(...transactions.map(tx => Math.abs(tx.amount)));
  }, [transactions]);

  const loadAnalyticsData = useCallback(async () => {
    if (!auth.user) return;

    setLoading(true);
    setError("");

    const loadTransactionsFallback = async () => {
      try {
        // Fallback: Load transactions and process them locally
        const response = await getTransactions(auth.user!.id, {}, 1, 1000);

        if (response.error) {
          setError(response.error);
        } else {
          setTransactions(response.data || []);
          // For fallback, we'll just set empty analytics data since the processAnalyticsData function is complex
          // and we want to encourage using the backend API instead
          setAnalyticsData(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics data');
      }
    };

    try {
      // Use unified workflow analytics processing with the analytics agent
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

      // The transactions processing endpoint expects a RawTransaction body.
      // Send the user's analytics request text in `description`, and pass mode/user_id as query params.
      const mode = 'full_pipeline';
      const userId = auth.user.id;

      const rawTransaction = {
        // Use ISO date for the transaction date (backend accepts string date)
        date: new Date().toISOString(),
        // Amount must be a string per RawTransaction schema; analytics request isn't a money tx so set 0
        amount: "0",
        // Put the analytics prompt in the description so the workflow can use it as user_input
        description: "Generate comprehensive analytics report with spending patterns, insights, and recommendations for my financial data",
        payment_method: "other",
        // Include the conversation context in metadata so the backend agents can access preferences
        metadata: {
          request_type: "analytics_generation",
          user_preferences: {
            analytics_focus: ["spending_patterns", "budget_recommendations", "savings_opportunities", "pattern_insights"]
          }
        }
      };

      const url = `${API_BASE}/api/v1/transactions/process?mode=${encodeURIComponent(mode)}&user_id=${encodeURIComponent(userId)}`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rawTransaction)
      });

      if (response.ok) {
        const workflowResult = await response.json();
        console.log('Unified Workflow Analytics Result:', workflowResult);

        if (workflowResult.result) {
          // Extract analytics data from unified workflow result
          const result = workflowResult.result;

          // Get pattern insights and spending patterns from workflow
          const spendingPatterns = result.spending_patterns || {};
          const patternInsights = result.pattern_insights || [];
          const budgetRecommendations = result.budget_recommendations || [];
          const spendingSuggestions = result.spending_suggestions || [];
          let processedTransactions = result.processed_transactions || [];

          // If the workflow didn't return processed transactions (new user / no data),
          // fall back to loading stored transactions from the backend and map them
          // into the same shape expected by the analytics code.
          if ((!processedTransactions || processedTransactions.length === 0)) {
            try {
              const txResp = await getTransactions(auth.user.id, {}, 1, 1000);
              if (!txResp.error) {
                const fetched = txResp.data || [];
                const fetchedTyped = fetched as Transaction[];
                // Map stored transactions to a minimal processed transaction shape
                processedTransactions = fetchedTyped.map((t) => ({
                  amount: t.amount,
                  date: t.date,
                  predicted_category: t.category,
                  category: t.category,
                  transaction_type: t.transaction_type || (t.amount < 0 ? 'expense' : 'income'),
                  description: t.description,
                  merchant: t.merchant
                }));
                // Update transactions state so Recent Transactions table shows them
                setTransactions(fetched);
              }
            } catch (e) {
              console.warn('Failed to load fallback transactions for analytics:', e);
            }
          }

          console.log('Workflow Analytics Data:', {
            spendingPatterns,
            patternInsightsCount: patternInsights.length,
            budgetRecommendationsCount: budgetRecommendations.length,
            spendingSuggestionsCount: spendingSuggestions.length,
            processedTransactionsCount: processedTransactions.length
          });

          // Calculate totals from processed transactions
          let totalIncome = 0;
          let totalExpenses = 0;
          const monthlyData: Record<string, { income: number; expenses: number }> = {};
          const categoryData: Record<string, { amount: number; count: number }> = {};

          processedTransactions.forEach((tx: Record<string, unknown>) => {
            const amount = Math.abs(Number(tx.amount) || 0);
            const date = new Date(String(tx.date));
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            const category = String(tx.predicted_category || tx.category || 'Uncategorized');

            if (!monthlyData[monthKey]) {
              monthlyData[monthKey] = { income: 0, expenses: 0 };
            }

            if (!categoryData[category]) {
              categoryData[category] = { amount: 0, count: 0 };
            }

            if ((tx.transaction_type || tx.type) === 'income' || amount < 0) {
              totalIncome += amount;
              monthlyData[monthKey].income += amount;
            } else {
              totalExpenses += amount;
              monthlyData[monthKey].expenses += amount;
              categoryData[category].amount += amount;
              categoryData[category].count += 1;
            }
          });

          // Convert workflow analytics data to frontend format
          const analyticsDataFromWorkflow: AnalyticsData = {
            totalIncome,
            totalExpenses,
            netCashflow: totalIncome - totalExpenses,
            transactionCount: processedTransactions.length,
            avgExpense: totalExpenses / Math.max(processedTransactions.length, 1),
            avgIncome: totalIncome / Math.max(processedTransactions.length, 1),

            monthlyData: Object.entries(monthlyData).map(([month, data]) => ({
              month,
              income: data.income,
              expenses: data.expenses,
              net: data.income - data.expenses
            })).sort((a, b) => a.month.localeCompare(b.month)),

            categoryData: Object.entries(categoryData).map(([category, data]) => ({
              category: category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' '),
              amount: data.amount,
              count: data.count,
              percentage: totalExpenses > 0 ? (data.amount / totalExpenses) * 100 : 0
            })).filter(item => item.amount > 0).sort((a, b) => b.amount - a.amount),

            dailyData: [],
            merchantData: [],
            weeklyPattern: [],
            recurringPayments: [],
            anomalies: [],

            // Convert AI insights from unified workflow
            insights: [
              ...patternInsights.map((insight: Record<string, unknown>) => ({
                type: String(insight.insight_type || 'pattern'),
                message: String(insight.description || 'Pattern insight generated'),
                severity: String(insight.severity || 'info')
              })),
              ...budgetRecommendations.map((rec: Record<string, unknown>) => ({
                type: 'budget_recommendation',
                message: String(rec.description || rec.title || 'Budget recommendation'),
                severity: 'info'
              })),
              ...spendingSuggestions.map((sugg: Record<string, unknown>) => ({
                type: 'spending_suggestion',
                message: String(sugg.description || sugg.title || 'Spending suggestion'),
                severity: 'info'
              }))
            ]
          };

          setAnalyticsData(analyticsDataFromWorkflow);
          setTransactions(processedTransactions);

        } else {
          console.error('No result data from unified workflow:', workflowResult);
          // Fallback to transaction-based processing if workflow doesn't return data
          await loadTransactionsFallback();
        }
      } else {
        // Fallback to transaction-based processing if workflow API not available
        console.warn('Unified workflow API not available, falling back to transaction processing');
        await loadTransactionsFallback();
      }
    } catch (err) {
      console.warn('Unified workflow analytics not available:', err);
      // Fallback to transaction-based processing
      await loadTransactionsFallback();
    }

    setLoading(false);
  }, [auth.user]);



  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      loadAnalyticsData();
    }
  }, [auth.isAuthenticated, auth.user, loadAnalyticsData]);

  // Re-load analytics when filters change
  useEffect(() => {
    if (auth.isAuthenticated && auth.user) {
      // Debounce the API call to avoid too many requests
      const timeoutId = setTimeout(() => {
        loadAnalyticsData();
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange, amountRange, selectedCategories]);

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
    return `LKR ${abs.toFixed(0)}`;
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
        ['Total Income', formatCurrency(analyticsData.totalIncome)],
        ['Total Expenses', formatCurrency(analyticsData.totalExpenses)],
        ['Net Cash Flow', formatCurrency(analyticsData.netCashflow)],
        ['Total Transactions', analyticsData.transactionCount.toString()],
        ['Average Expense', formatCurrency(analyticsData.avgExpense)],
        ['Average Income', formatCurrency(analyticsData.avgIncome)],
        ['Expense Ratio', `${analyticsData.totalIncome > 0 ? ((analyticsData.totalExpenses / analyticsData.totalIncome) * 100).toFixed(1) : 0}%`],
        ['Savings Rate', `${analyticsData.totalIncome > 0 ? ((analyticsData.netCashflow / analyticsData.totalIncome) * 100).toFixed(1) : 0}%`]
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

      const categoryTableData = analyticsData.categoryData
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

       // Add report description
       pdf.setFontSize(12);
       pdf.setTextColor(100);
       pdf.text('This report analyzes your spending patterns across different days, categories, and behavioral trends.', 20, yPosition);
       yPosition += 20;

       // Weekly pattern analysis
       const highestDay = analyticsData.weeklyPattern.reduce((prev, current) =>
         (prev.amount > current.amount) ? prev : current);
       const lowestDay = analyticsData.weeklyPattern.reduce((prev, current) =>
         (prev.amount < current.amount) ? prev : current);

       const weekendSpending = analyticsData.weeklyPattern
         .filter(d => d.day === 'Saturday' || d.day === 'Sunday')
         .reduce((sum, d) => sum + d.amount, 0);
       const weekdaySpending = analyticsData.weeklyPattern
         .filter(d => !['Saturday', 'Sunday'].includes(d.day))
         .reduce((sum, d) => sum + d.amount, 0);

       // Pattern Summary Section
       pdf.setFontSize(16);
       pdf.setTextColor(40);
       pdf.text('Pattern Summary', 20, yPosition);
       yPosition += 10;

       const patternData = [
         ['Pattern Metric', 'Value'],
         ['Total Transactions Analyzed', analyticsData.transactionCount.toString()],
         ['Highest Spending Day', `${highestDay.day} (${formatCurrency(highestDay.amount)})`],
         ['Lowest Spending Day', `${lowestDay.day} (${formatCurrency(lowestDay.amount)})`],
         ['Top Spending Category', analyticsData.categoryData[0]?.category || 'N/A'],
         ['Top Category Amount', formatCurrency(analyticsData.categoryData[0]?.amount || 0)],
         ['Weekend vs Weekday Ratio', `${weekdaySpending > 0 ? ((weekendSpending / weekdaySpending) * 100).toFixed(1) : 0}%`],
         ['Average Daily Spending', formatCurrency(analyticsData.totalExpenses / 7)],
         ['Most Active Day', `${highestDay.day} with ${Math.round(analyticsData.transactionCount / 7)} transactions`]
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

       const dowData = analyticsData.weeklyPattern.map(day => {
         const dayTransactions = Math.round(analyticsData.transactionCount / 7); // Simplified calculation
         const avgPerTransaction = day.amount / dayTransactions || 0;
         return [
           day.day,
           formatCurrency(day.amount),
           `${((day.amount / analyticsData.totalExpenses) * 100).toFixed(1)}%`,
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

       const topCategoriesData = analyticsData.categoryData.slice(0, 5).map((cat, index) => [
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

       const topCategoryPercentage = analyticsData.categoryData[0]?.percentage || 0;
       if (topCategoryPercentage > 40) {
         behaviorInsights.push(['Category Concentration', `${topCategoryPercentage.toFixed(0)}% spent on ${analyticsData.categoryData[0]?.category}`, 'Consider diversifying expenses']);
       }

       if (highestDay.amount > (analyticsData.totalExpenses / 7) * 2) {
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
      const dailyAmounts = analyticsData.dailyData.map(d => d.amount);
      const trendDirection = dailyAmounts.length > 1 ?
        (dailyAmounts[dailyAmounts.length - 1] > dailyAmounts[0] ? 'Increasing' : 'Decreasing') : 'Stable';
      const avgDaily = dailyAmounts.reduce((sum, amt) => sum + amt, 0) / dailyAmounts.length;
      const volatility = dailyAmounts.length > 1 ?
        Math.sqrt(dailyAmounts.reduce((sum, amt) => sum + Math.pow(amt - avgDaily, 2), 0) / dailyAmounts.length) / avgDaily * 100 : 0;

      const trendsData = [
        ['Trend Metric', 'Value'],
        ['Overall Trend Direction', trendDirection],
        ['Average Daily Spending', formatCurrency(avgDaily)],
        ['Spending Volatility', `${volatility.toFixed(1)}%`],
        ['Analysis Period (Days)', analyticsData.dailyData.length.toString()],
        ['Highest Daily Spending', formatCurrency(Math.max(...dailyAmounts))],
        ['Lowest Daily Spending', formatCurrency(Math.min(...dailyAmounts))],
        ['7-Day Moving Average (Latest)', formatCurrency(analyticsData.dailyData[analyticsData.dailyData.length - 1]?.ma7 || 0)]
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

      const topMerchant = analyticsData.merchantData[0];
      const merchantCount = analyticsData.merchantData.length;
      const avgMerchantSpending = analyticsData.merchantData.reduce((sum, m) => sum + m.totalSpent, 0) / merchantCount;

      const merchantSummaryData = [
        ['Merchant Metric', 'Value'],
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

      const topMerchantsData = analyticsData.merchantData
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
        head: [['Rank', 'Merchant', 'Total Spent', 'Avg Transaction', 'Visit Count']],
        body: topMerchantsData,
        theme: 'striped',
        headStyles: { fillColor: [231, 76, 60] },
        columnStyles: {
          0: { cellWidth: 15 },
          1: { cellWidth: 50 },
          2: { cellWidth: 35 },
          3: { cellWidth: 35 },
          4: { cellWidth: 25 }
        }
      });

    } else if (selectedAnalysis === "predictions") {
      // Predictive Analytics Report
      pdf.setFontSize(16);
      pdf.setTextColor(40);
      pdf.text('Predictive Financial Analysis', 20, yPosition);
      yPosition += 10;

      // Calculate forecast data
      const recentDays = analyticsData.dailyData.slice(-30);
      const recentTrend = recentDays.reduce((sum, d) => sum + d.amount, 0) / recentDays.length;
      const historicalAvg = analyticsData.dailyData.reduce((sum, d) => sum + d.amount, 0) / analyticsData.dailyData.length;
      const trendChange = historicalAvg > 0 ? ((recentTrend - historicalAvg) / historicalAvg * 100) : 0;

      const forecast30Days = recentTrend * 30;
      const confidence = Math.max(0.4, Math.min(0.95, analyticsData.dailyData.length / 60));

      const predictiveData = [
        ['Predictive Metric', 'Value'],
        ['Historical Daily Average', formatCurrency(historicalAvg)],
        ['Recent Trend (30 days)', `${formatCurrency(recentTrend)}/day`],
        ['Trend Direction', trendChange > 0 ? 'Increasing' : trendChange < 0 ? 'Decreasing' : 'Stable'],
        ['30-Day Forecast', formatCurrency(forecast30Days)],
        ['Predicted Monthly Change', `${trendChange > 0 ? '+' : ''}${trendChange.toFixed(1)}%`],
        ['Forecast Confidence', `${(confidence * 100).toFixed(0)}%`],
        ['Data Points Used', `${analyticsData.dailyData.length} days`]
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
                  setAmountRange({ min: 0, max: maxAmount });
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
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Advanced Analytics
              </h1>
              <p className="text-slate-600 mt-2 text-lg">AI-Powered Financial Intelligence & Insights</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={generatePDFReport}
                className="flex items-center space-x-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-4 py-2 rounded-lg transition-colors duration-200"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
                <span className="text-sm font-medium">Export PDF</span>
              </button>
              <div className="hidden md:flex items-center space-x-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white px-4 py-2 rounded-full">
                <SparklesIcon className="w-4 h-4" />
                <span className="text-sm font-medium">AI Analytics</span>
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <FunnelIcon className="h-6 w-6 mr-2 text-blue-600" />
            Analytics Controls
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
            </div>

            {/* Amount Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Amount Range</label>
              <div className="space-y-2">
                <input
                  type="number"
                  placeholder="Min Amount"
                  value={amountRange.min}
                  onChange={(e) => setAmountRange(prev => ({ ...prev, min: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  step="10"
                />
                <input
                  type="number"
                  placeholder="Max Amount"
                  value={amountRange.max}
                  onChange={(e) => setAmountRange(prev => ({ ...prev, max: parseFloat(e.target.value) || maxAmount }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  step="10"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Type Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {ANALYSIS_TYPES.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.id}
                    onClick={() => setSelectedAnalysis(type.id)}
                    className={`${
                      selectedAnalysis === type.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {type.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content based on selected analysis */}
        {selectedAnalysis === "overview" && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Expenses</p>
                    <p className="text-2xl font-bold text-red-600">{formatCurrencyCompact(analyticsData.totalExpenses)}</p>
                    <p className="text-xs text-gray-500">{analyticsData.transactionCount} transactions</p>
                  </div>
                  <ArrowTrendingDownIcon className="h-8 w-8 text-red-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Income</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrencyCompact(analyticsData.totalIncome)}</p>
                    <p className="text-xs text-gray-500">Revenue streams</p>
                  </div>
                  <ArrowTrendingUpIcon className="h-8 w-8 text-green-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Net Cash Flow</p>
                    <p className={`text-2xl font-bold ${analyticsData.netCashflow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrencyCompact(analyticsData.netCashflow)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {analyticsData.totalIncome > 0 ?
                        `${((analyticsData.netCashflow / analyticsData.totalIncome) * 100).toFixed(1)}%` :
                        '0%'
                      } savings rate
                    </p>
                  </div>
                  <BanknotesIcon className="h-8 w-8 text-blue-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div>
                  <p className="text-sm text-gray-600">Avg Expense</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrencyCompact(analyticsData.avgExpense)}</p>
                  <p className="text-xs text-gray-500">Per transaction</p>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div>
                  <p className="text-sm text-gray-600">Avg Income</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrencyCompact(analyticsData.avgIncome)}</p>
                  <p className="text-xs text-gray-500">Per transaction</p>
                </div>
              </div>
            </div>



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
                        { name: 'Income', value: analyticsData.totalIncome, fill: '#10B981' },
                        { name: 'Expenses', value: analyticsData.totalExpenses, fill: '#EF4444' }
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
                    { type: 'Income', amount: analyticsData.totalIncome },
                    { type: 'Expenses', amount: analyticsData.totalExpenses }
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
                <BarChart data={analyticsData.monthlyData}>
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
                  <BarChart data={analyticsData.weeklyPattern}>
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
                  <BarChart data={analyticsData.categoryData.slice(0, 8)} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={formatCurrencyCompact} />
                    <YAxis dataKey="category" type="category" width={100} />
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
                      data={analyticsData.categoryData.slice(0, 6)}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="amount"
                      label={({ category, percentage }) => `${category}: ${percentage.toFixed(1)}%`}
                    >
                      {analyticsData.categoryData.slice(0, 6).map((entry, index) => (
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
                  {analyticsData.categoryData.slice(0, 5).map((category, index) => (
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
                <LineChart data={analyticsData.dailyData}>
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
                  <LineChart data={analyticsData.monthlyData}>
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
                  <BarChart data={analyticsData.weeklyPattern}>
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
                  <BarChart data={analyticsData.merchantData} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={formatCurrencyCompact} />
                    <YAxis dataKey="merchant" type="category" width={120} />
                    <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Total Spent']} />
                    <Bar dataKey="totalSpent" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Merchant Analysis: Frequency vs Spending</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart data={analyticsData.merchantData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="count" name="Transaction Count" />
                    <YAxis dataKey="totalSpent" name="Total Spent" tickFormatter={formatCurrencyCompact} />
                    <Tooltip
                      formatter={(value, name) => {
                        const displayValue = name === 'totalSpent' ? formatCurrency(Number(value)) : value;
                        const displayName = name === 'totalSpent' ? 'Total Spent' : 'Transaction Count';
                        return [displayValue, displayName];
                      }}
                      labelFormatter={(label) => `Merchant: ${label}`}
                    />
                    <Scatter dataKey="totalSpent" fill="#3B82F6" />
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
                    {analyticsData.merchantData.map((merchant, index) => (
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
                    {formatCurrency(analyticsData.dailyData.slice(-30).reduce((sum, d) => sum + d.amount, 0))}
                  </div>
                  <div className="text-sm text-gray-600">Recent Monthly Spending</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {analyticsData.dailyData.length > 7 ?
                      `${((analyticsData.dailyData.slice(-7).reduce((sum, d) => sum + d.amount, 0) /
                          Math.max(1, analyticsData.dailyData.slice(-14, -7).reduce((sum, d) => sum + d.amount, 0)) - 1) * 100).toFixed(1)}%`
                      : '0%'}
                  </div>
                  <div className="text-sm text-gray-600">Weekly Change</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.min(95, Math.max(40, analyticsData.dailyData.length * 2))}%
                  </div>
                  <div className="text-sm text-gray-600">Data Confidence</div>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={[
                  ...analyticsData.dailyData.slice(-30),
                  ...Array.from({ length: 30 }, (_, i) => ({
                    date: format(addDays(new Date(), i + 1), 'yyyy-MM-dd'),
                    amount: analyticsData.dailyData.slice(-1)[0]?.amount * (1 + Math.random() * 0.2 - 0.1) || 0,
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
