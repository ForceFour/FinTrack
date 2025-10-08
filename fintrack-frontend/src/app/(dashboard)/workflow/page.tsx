"use client";

import { useState, useEffect } from "react";
import AgentStatusWidget from "@/components/AgentStatusWidget";
import {
  PlayIcon,
  ArrowPathIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface WorkflowStatus {
  workflow_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  current_agent?: string;
  progress: number;
  start_time: string;
  end_time?: string;
  result?: Record<string, unknown>;
}

interface ProcessingLog {
  timestamp: string;
  file: string;
  transactions: number;
  status: string;
  workflow_id?: string;
}

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [processingLogs, setProcessingLogs] = useState<ProcessingLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkflowData();
    // Set up polling for real-time updates
    const interval = setInterval(loadWorkflowData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadWorkflowData = async () => {
    try {
      // Load workflow statistics (using mock data for now)
      // const statsResponse = await apiClient.request("/workflow/statistics");

      // Mock workflow data
      const mockWorkflows: WorkflowStatus[] = [
        {
          workflow_id: "wf_001",
          status: "completed",
          current_agent: "safety_guard",
          progress: 100,
          start_time: new Date(Date.now() - 300000).toISOString(),
          end_time: new Date().toISOString(),
          result: { transactions_processed: 150, insights_generated: 12 }
        },
        {
          workflow_id: "wf_002",
          status: "processing",
          current_agent: "pattern_analyzer",
          progress: 75,
          start_time: new Date(Date.now() - 120000).toISOString(),
          result: { transactions_processed: 89 }
        }
      ];
      setWorkflows(mockWorkflows);

      // Load processing logs (mock data for now)
      const mockLogs: ProcessingLog[] = [
        {
          timestamp: new Date(Date.now() - 300000).toISOString(),
          file: "transactions_january.csv",
          transactions: 150,
          status: "completed",
          workflow_id: "wf_001"
        },
        {
          timestamp: new Date(Date.now() - 120000).toISOString(),
          file: "bank_statement_feb.xlsx",
          transactions: 89,
          status: "processing",
          workflow_id: "wf_002"
        },
        {
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          file: "credit_card_dec.csv",
          transactions: 234,
          status: "completed",
          workflow_id: "wf_003"
        }
      ];
      setProcessingLogs(mockLogs);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Agent Workflow Monitor</h1>
        <p className="text-gray-600 mt-2">
          Real-time monitoring of AI agent processing pipelines
        </p>
      </div>

      {/* Agent Status Overview */}
      <AgentStatusWidget />

      {/* Workflow Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {workflows.filter(w => w.status === "completed").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <PlayIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Processing</p>
              <p className="text-2xl font-bold text-gray-900">
                {workflows.filter(w => w.status === "processing").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <ClockIcon className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">
                {workflows.filter(w => w.status === "pending").length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <XCircleIcon className="h-8 w-8 text-red-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-gray-900">
                {workflows.filter(w => w.status === "failed").length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Workflows */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Active Workflows</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {workflows.map((workflow) => (
            <div key={workflow.workflow_id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(workflow.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Workflow {workflow.workflow_id}
                    </p>
                    <p className="text-sm text-gray-500">
                      {workflow.current_agent ? `Current: ${workflow.current_agent.replace('_', ' ')}` : 'Initializing...'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${workflow.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{workflow.progress}%</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(workflow.status)}`}>
                    {workflow.status}
                  </span>
                </div>
              </div>
              <div className="mt-4 flex justify-between text-sm text-gray-500">
                <span>Started: {new Date(workflow.start_time).toLocaleString()}</span>
                <span>Duration: {formatDuration(workflow.start_time, workflow.end_time)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Processing Log */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Processing History</h3>
            <button
              onClick={loadWorkflowData}
              className="flex items-center px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4 mr-1" />
              Refresh
            </button>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {processingLogs.map((log, index) => (
            <div key={index} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(log.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{log.file}</p>
                    <p className="text-sm text-gray-500">
                      {log.transactions} transactions • {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(log.status)}`}>
                  {log.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Communication Log */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Agent Communication</h3>
        </div>
        <div className="p-6">
          <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm">
            <div className="space-y-2">
              <div className="text-green-600">
                [2025-10-08 13:45:23] Ingestion → NER/Merchant: Processed 150 transactions successfully
              </div>
              <div className="text-blue-600">
                [2025-10-08 13:45:24] NER/Merchant → Classifier: Identified 45 unique merchants
              </div>
              <div className="text-purple-600">
                [2025-10-08 13:45:26] Classifier → Pattern Analyzer: Categorized into 12 transaction types
              </div>
              <div className="text-orange-600">
                [2025-10-08 13:45:28] Pattern Analyzer → Suggestion: Detected 8 spending patterns
              </div>
              <div className="text-indigo-600">
                [2025-10-08 13:45:30] Suggestion → Safety Guard: Generated 5 personalized recommendations
              </div>
              <div className="text-green-600">
                [2025-10-08 13:45:32] Safety Guard → System: Security validation passed - no anomalies detected
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
