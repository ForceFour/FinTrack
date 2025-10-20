"use client";
import { useState, useEffect } from "react";
import {
  PlayIcon,
  ArrowPathIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { apiClient } from "@/lib/api-client";
import { supabase } from "@/lib/supabase";
import type {
  WorkflowStatusData,
  ProcessingLog,
  WorkflowStatistics,
  WorkflowStatisticsResponse,
  ActiveWorkflowsResponse,
  WorkflowHistoryResponse,
  AgentCommunication,
  AgentCommunicationsResponse,
} from "@/lib/types/workflow";

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState<WorkflowStatusData[]>([]);
  const [processingLogs, setProcessingLogs] = useState<ProcessingLog[]>([]);
  const [communications, setCommunications] = useState<AgentCommunication[]>([]);
  const [statistics, setStatistics] = useState<WorkflowStatistics>({
    total: 0,
    completed: 0,
    processing: 0,
    pending: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    initializeUser();
  }, []);

  useEffect(() => {
    if (userId) {
      loadWorkflowData();
      // Set up polling for real-time updates
      const interval = setInterval(loadWorkflowData, 5000);
      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const initializeUser = async () => {
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) {
        setUserId(user.id);
      }
    } catch (error) {
      console.error("Failed to get user:", error);
    }
  };

  const loadWorkflowData = async () => {
    if (!userId) return;

    try {
      // Load workflow statistics
      const statsResponse = await apiClient.getWorkflowStatistics(userId);
      if (statsResponse.status === "success" && statsResponse.data) {
        const data = statsResponse.data as WorkflowStatisticsResponse;
        setStatistics(data.statistics);
      }

      // Load active workflows
      const workflowsResponse = await apiClient.getActiveWorkflows(userId, 10);
      if (workflowsResponse.status === "success" && workflowsResponse.data) {
        const data = workflowsResponse.data as ActiveWorkflowsResponse;
        setWorkflows(data.workflows);
      }

      // Load processing history
      const historyResponse = await apiClient.getWorkflowHistory(userId, 20);
      if (historyResponse.status === "success" && historyResponse.data) {
        const data = historyResponse.data as WorkflowHistoryResponse;
        setProcessingLogs(data.history);
      }

      // Load agent communications
      const commsResponse = await apiClient.getAgentCommunications(userId, 50);
      if (commsResponse.status === "success" && commsResponse.data) {
        const data = commsResponse.data as AgentCommunicationsResponse;
        setCommunications(data.communications);
      }
    } catch (error) {
      console.error("Failed to load workflow data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case "processing":
        return <PlayIcon className="h-5 w-5 text-blue-500" />;
      case "failed":
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case "pending":
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-700 bg-green-100";
      case "processing":
        return "text-blue-700 bg-blue-100";
      case "failed":
        return "text-red-700 bg-red-100";
      case "pending":
        return "text-yellow-700 bg-yellow-100";
      default:
        return "text-gray-700 bg-gray-100";
    }
  };

  const getCommunicationStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "success":
      case "completed":
        return "text-green-600";
      case "info":
      case "processing":
        return "text-blue-600";
      case "warning":
        return "text-orange-600";
      case "error":
      case "failed":
        return "text-red-600";
      default:
        return "text-purple-600";
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start);
    const endTime = end ? new Date(end) : new Date();
    const duration = endTime.getTime() - startTime.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!userId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <p className="text-slate-600">Please log in to view workflows</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Hero Header Section */}
        <div className="relative bg-white rounded-3xl shadow-2xl p-6 md:p-8 lg:p-10 border border-slate-200 overflow-hidden">
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-indigo-400/20 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-purple-400/20 to-pink-400/20 rounded-full blur-3xl -ml-24 -mb-24"></div>

          <div className="relative z-10">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl blur-lg opacity-50 animate-pulse"></div>
                    <div className="relative p-3 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
                      <PlayIcon className="w-8 h-8 text-white" />
                    </div>
                  </div>
                  <div>
                    <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      AI Workflow Monitor
                    </h1>
                  </div>
                </div>
                <p className="text-slate-600 text-base md:text-lg leading-relaxed max-w-3xl">
                  Real-time monitoring of AI agent processing pipelines and transaction workflows
                </p>
              </div>

              <button
                onClick={loadWorkflowData}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-2xl hover:from-blue-600 hover:to-indigo-700 transition-all font-medium flex items-center space-x-2 shadow-lg hover:shadow-xl"
              >
                <ArrowPathIcon className="w-5 h-5" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Workflow Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-6">
          <div className="bg-white p-6 rounded-3xl shadow-xl border border-slate-200 hover:shadow-2xl transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl shadow-lg">
                <CheckCircleIcon className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Completed</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                  {statistics.completed}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl shadow-xl border border-slate-200 hover:shadow-2xl transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl shadow-lg">
                <PlayIcon className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Processing</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                  {statistics.processing}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl shadow-xl border border-slate-200 hover:shadow-2xl transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl shadow-lg">
                <ClockIcon className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Pending</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">
                  {statistics.pending}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-3xl shadow-xl border border-slate-200 hover:shadow-2xl transition-shadow">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-red-500 to-pink-500 rounded-xl shadow-lg">
                <XCircleIcon className="h-7 w-7 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500">Failed</p>
                <p className="text-3xl font-bold bg-gradient-to-r from-red-600 to-pink-600 bg-clip-text text-transparent">
                  {statistics.failed}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Active Workflows and Processing History - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Workflows */}
          <div className="bg-white rounded-3xl shadow-xl border border-slate-200">
            <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-indigo-50">
              <h3 className="text-xl font-bold text-slate-900">Active Workflows</h3>
              <p className="text-sm text-slate-600 mt-1">Currently processing transactions</p>
            </div>
            <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
              {workflows.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="mx-auto w-16 h-16 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center mb-4">
                    <PlayIcon className="h-8 w-8 text-slate-400" />
                  </div>
                  <p className="text-slate-500 font-medium">No active workflows found</p>
                  <p className="text-sm text-slate-400 mt-1">Upload transactions to start processing</p>
                </div>
              ) : (
                workflows.map((workflow) => (
                  <div key={workflow.workflow_id} className="p-6 hover:bg-gradient-to-r hover:from-blue-50 hover:to-transparent transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(workflow.status)}
                        <div>
                          <div className="font-semibold text-slate-900">
                            {workflow.workflow_id.substring(0, 16)}...
                          </div>
                          <div className="text-sm text-slate-500 mt-1">
                            Current Agent: <span className="font-medium text-slate-700">{workflow.current_agent || "Initializing"}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <span
                            className={`px-3 py-1.5 rounded-xl text-xs font-semibold shadow-sm ${getStatusColor(
                              workflow.status
                            )}`}
                          >
                            {workflow.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="w-48">
                          <div className="flex justify-between text-xs font-medium text-slate-600 mb-1.5">
                            <span>Progress</span>
                            <span className="text-blue-600">{workflow.progress}%</span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2.5 shadow-inner">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2.5 rounded-full transition-all shadow-sm"
                              style={{ width: `${workflow.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex justify-between text-sm text-slate-500">
                      <span>Started: <span className="font-medium text-slate-700">{formatTimestamp(workflow.start_time)}</span></span>
                      <span>Duration: <span className="font-medium text-slate-700">{formatDuration(workflow.start_time, workflow.end_time)}</span></span>
                    </div>
                    {workflow.result && (
                      <div className="mt-3 flex gap-4 text-xs">
                        <span className="text-slate-600">Transactions: <span className="font-semibold text-slate-900">{workflow.result.transactions_processed}</span></span>
                        <span className="text-slate-600">Insights: <span className="font-semibold text-slate-900">{workflow.result.insights_generated}</span></span>
                        <span className="text-slate-600">Suggestions: <span className="font-semibold text-slate-900">{workflow.result.suggestions_count}</span></span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Processing History */}
          <div className="bg-white rounded-3xl shadow-xl border border-slate-200">
            <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-purple-50 to-pink-50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-slate-900">Processing History</h3>
                  <p className="text-sm text-slate-600 mt-1">Recent transaction processing</p>
                </div>
                <button
                  onClick={loadWorkflowData}
                  className="flex items-center px-3 py-2 text-sm bg-white hover:bg-slate-50 rounded-xl transition-colors shadow-sm border border-slate-200"
                >
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                  Refresh
                </button>
              </div>
            </div>
            <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
              {processingLogs.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="mx-auto w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mb-4">
                    <ClockIcon className="h-8 w-8 text-purple-400" />
                  </div>
                  <p className="text-slate-500 font-medium">No processing history available</p>
                  <p className="text-sm text-slate-400 mt-1">Completed workflows will appear here</p>
                </div>
              ) : (
                processingLogs.map((log, index) => (
                  <div key={index} className="p-4 hover:bg-gradient-to-r hover:from-purple-50 hover:to-transparent transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(log.status)}
                        <div>
                          <div className="font-semibold text-slate-900">
                            {log.source_name || log.file || "Unknown Source"}
                          </div>
                          <div className="text-sm text-slate-500 mt-1">
                            {formatTimestamp(log.timestamp)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-slate-700 mb-1">
                          {log.transactions} transactions
                        </div>
                        <span
                          className={`px-2 py-1 rounded-xl text-xs font-semibold shadow-sm ${getStatusColor(
                            log.status
                          )}`}
                        >
                          {log.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Agent Communication Log */}
        <div className="bg-white rounded-3xl shadow-xl border border-slate-200">
          <div className="p-6 border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-teal-50">
            <h3 className="text-xl font-bold text-slate-900">Agent Communication</h3>
            <p className="text-sm text-slate-600 mt-1">Real-time agent interactions grouped by workflow</p>
          </div>
          <div className="p-6">
            {communications.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {(() => {
                  // Group communications by workflow_id
                  const grouped = communications.reduce((acc, comm) => {
                    if (!acc[comm.workflow_id]) {
                      acc[comm.workflow_id] = [];
                    }
                    acc[comm.workflow_id].push(comm);
                    return acc;
                  }, {} as Record<string, typeof communications>);

                  return Object.entries(grouped).map(([workflowId, comms]) => (
                    <div key={workflowId} className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-4 border border-slate-200 shadow-sm">
                      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-300">
                        <div className="flex items-center space-x-2">
                          <div className="w-2.5 h-2.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full shadow-sm"></div>
                          <span className="font-bold text-slate-700">
                            Workflow {workflowId}
                          </span>
                        </div>
                        <span className="text-xs font-medium text-slate-500 bg-white px-2 py-1 rounded-lg">
                          {comms.length} {comms.length === 1 ? 'stage' : 'stages'}
                        </span>
                      </div>
                      <div className="space-y-1.5 font-mono text-xs">
                        {comms
                          .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
                          .map((comm, index) => (
                            <div
                              key={`${comm.workflow_id}-${comm.stage}-${index}`}
                              className={`${getCommunicationStatusColor(comm.status)} py-1.5 px-2 rounded-lg`}
                            >
                              <span className="text-slate-400">[{formatTimestamp(comm.timestamp)}]</span>{" "}
                              <span className="font-bold text-slate-700">{comm.agent}:</span> <span className="text-slate-600">{comm.message}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            ) : (
              <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl p-12 text-center border border-slate-200">
                <div className="mx-auto w-16 h-16 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-2xl flex items-center justify-center mb-4">
                  <ExclamationTriangleIcon className="h-8 w-8 text-emerald-400" />
                </div>
                <p className="text-slate-500 font-medium">No agent communications yet</p>
                <p className="text-sm text-slate-400 mt-1">Upload transactions to see real-time agent interactions</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
