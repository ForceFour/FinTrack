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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl shadow-lg">
                  <PlayIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Agent Workflow Monitor
                  </h1>
                  <p className="text-slate-600 mt-1 text-lg">
                    Real-time monitoring of AI agent processing pipelines
                  </p>
                </div>
              </div>
            </div>
            <div className="hidden md:flex space-x-3">
              <button
                onClick={loadWorkflowData}
                className="px-6 py-3 bg-white border-2 border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 transition-all font-medium flex items-center space-x-2"
              >
                <ArrowPathIcon className="w-5 h-5" />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Workflow Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Completed</p>
                <p className="text-2xl font-bold text-slate-900">
                  {statistics.completed}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <div className="flex items-center">
              <PlayIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Processing</p>
                <p className="text-2xl font-bold text-slate-900">
                  {statistics.processing}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Pending</p>
                <p className="text-2xl font-bold text-slate-900">
                  {statistics.pending}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-lg border border-slate-200">
            <div className="flex items-center">
              <XCircleIcon className="h-8 w-8 text-red-500" />
              <div className="ml-4">
                <p className="text-sm font-medium text-slate-600">Failed</p>
                <p className="text-2xl font-bold text-slate-900">
                  {statistics.failed}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Active Workflows and Processing History - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Workflows */}
          <div className="bg-white rounded-2xl shadow-lg border border-slate-200">
            <div className="p-6 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900">Active Workflows</h3>
            </div>
            <div className="divide-y divide-slate-200 max-h-[600px] overflow-y-auto">
              {workflows.length === 0 ? (
                <div className="p-6 text-center text-slate-500">
                  No active workflows found. Upload transactions to start processing.
                </div>
              ) : (
                workflows.map((workflow) => (
                  <div key={workflow.workflow_id} className="p-6 hover:bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(workflow.status)}
                        <div>
                          <div className="font-medium text-slate-900">
                            {workflow.workflow_id.substring(0, 16)}...
                          </div>
                          <div className="text-sm text-slate-500">
                            Current Agent: {workflow.current_agent || "Initializing"}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                              workflow.status
                            )}`}
                          >
                            {workflow.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="w-48">
                          <div className="flex justify-between text-xs text-slate-600 mb-1">
                            <span>Progress</span>
                            <span>{workflow.progress}%</span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${workflow.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex justify-between text-sm text-slate-500">
                      <span>Started: {formatTimestamp(workflow.start_time)}</span>
                      <span>Duration: {formatDuration(workflow.start_time, workflow.end_time)}</span>
                    </div>
                    {workflow.result && (
                      <div className="mt-3 flex gap-4 text-xs text-slate-600">
                        <span>Transactions: {workflow.result.transactions_processed}</span>
                        <span>Insights: {workflow.result.insights_generated}</span>
                        <span>Suggestions: {workflow.result.suggestions_count}</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Processing History */}
          <div className="bg-white rounded-2xl shadow-lg border border-slate-200">
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Processing History</h3>
                <button
                  onClick={loadWorkflowData}
                  className="flex items-center px-3 py-1 text-sm bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
                >
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                  Refresh
                </button>
              </div>
            </div>
            <div className="divide-y divide-slate-200 max-h-[600px] overflow-y-auto">
              {processingLogs.length === 0 ? (
                <div className="p-6 text-center text-slate-500">
                  No processing history available.
                </div>
              ) : (
                processingLogs.map((log, index) => (
                  <div key={index} className="p-4 hover:bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(log.status)}
                        <div>
                          <div className="font-medium text-slate-900">
                            {log.source_name || log.file || "Unknown Source"}
                          </div>
                          <div className="text-sm text-slate-500">
                            {formatTimestamp(log.timestamp)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-slate-700">
                          {log.transactions} transactions
                        </div>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
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
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200">
          <div className="p-6 border-b border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900">Agent Communication</h3>
            <p className="text-sm text-slate-500 mt-1">Real-time agent interactions grouped by workflow</p>
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
                    <div key={workflowId} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-300">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span className="font-semibold text-slate-700">
                            Workflow {workflowId}
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">
                          {comms.length} {comms.length === 1 ? 'stage' : 'stages'}
                        </span>
                      </div>
                      <div className="space-y-1 font-mono text-xs">
                        {comms
                          .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
                          .map((comm, index) => (
                            <div
                              key={`${comm.workflow_id}-${comm.stage}-${index}`}
                              className={`${getCommunicationStatusColor(comm.status)} py-1`}
                            >
                              <span className="text-slate-400">[{formatTimestamp(comm.timestamp)}]</span>{" "}
                              <span className="font-semibold">{comm.agent}:</span> {comm.message}
                            </div>
                          ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            ) : (
              <div className="bg-slate-50 rounded-lg p-8 text-center">
                <p className="text-slate-500">No agent communications yet. Upload transactions to see real-time agent interactions.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
