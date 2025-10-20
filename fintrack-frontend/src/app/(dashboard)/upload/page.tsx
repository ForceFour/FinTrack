"use client";

import { useState, useRef, ChangeEvent } from "react";
import { useApp } from "@/app/providers";
import { apiClient } from "@/lib/api-client";
import {
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import AgentStatusWidget from "@/components/AgentStatusWidget";
import ConversationalEntry from "@/components/ConversationalEntry";
import { AgentStatus } from "@/lib/types";

interface UploadResult {
  transactions_processed?: number;
  new_transactions?: number;
  duplicates_found?: number;
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { refreshTransactions, auth } = useApp();

  // Separate agent status for file uploads and chat
  const [uploadAgentStatus, setUploadAgentStatus] = useState<AgentStatus>({
    ingestion: "idle",
    ner_merchant: "idle",
    classifier: "idle",
    pattern_analyzer: "idle",
    suggestion: "idle",
    safety_guard: "idle",
  });

  const [chatAgentStatus, setChatAgentStatus] = useState<AgentStatus>({
    ingestion: "idle",
    ner_merchant: "idle",
    classifier: "idle",
    pattern_analyzer: "idle",
    suggestion: "idle",
    safety_guard: "idle",
  });

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError("");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      setFile(files[0]);
      setResult(null);
      setError("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError("");
    setProgress(0);

    // Simulate agent pipeline progress
    const agents = [
      "ingestion",
      "ner_merchant",
      "classifier",
      "pattern_analyzer",
      "suggestion",
      "safety_guard",
    ];

    // Start agents for upload
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    // Update upload agent status sequentially
    for (let i = 0; i < agents.length; i++) {
      setUploadAgentStatus(prev => ({ ...prev, [agents[i]]: "running" }));
      await new Promise((resolve) => setTimeout(resolve, 800));
      setUploadAgentStatus(prev => ({ ...prev, [agents[i]]: "complete" }));
    }

    try {
      // Check if user is authenticated
      if (!auth.user?.id) {
        throw new Error("Please log in to upload transactions");
      }

      // Create a new File object to avoid reference issues
      const fileToUpload = new File([file], file.name, { type: file.type });

      // Upload file to backend API for AI processing
      const response = await apiClient.uploadTransactions(fileToUpload, auth.user.id);

      if (response.status === "error") {
        throw new Error(response.error || "Upload failed");
      }

      const uploadResult = response.data;

      setResult({
        transactions_processed: uploadResult.transactions_processed || 0,
        new_transactions: uploadResult.new_transactions || 0,
        duplicates_found: uploadResult.duplicates_found || 0,
      });

      // Refresh transactions in dashboard
      if (uploadResult.new_transactions > 0) {
        refreshTransactions();
      }

      setProgress(100);

    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
      agents.forEach((agent) => setUploadAgentStatus(prev => ({ ...prev, [agent]: "error" })));
    } finally {
      clearInterval(progressInterval);
      setUploading(false);

      // Reset upload agents to idle after a delay
      setTimeout(() => {
        setUploadAgentStatus({
          ingestion: "idle",
          ner_merchant: "idle",
          classifier: "idle",
          pattern_analyzer: "idle",
          suggestion: "idle",
          safety_guard: "idle",
        });
      }, 3000);
    }
  };



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Upload & Process Transactions
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                AI-Powered Transaction Processing & Analysis
              </p>
            </div>
            <div className="hidden md:block">
              <div className="flex items-center space-x-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-full">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                <span className="text-sm font-medium">AI Ready</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="space-y-8">
          {/* Row 1: File Upload + Agent Status */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* File Upload Section */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200 min-h-[600px] flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-slate-800">Upload Transaction File</h3>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-slate-600">Secure Upload</span>
                </div>
              </div>

              <div className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
                isDragOver
                  ? 'border-blue-400 bg-gradient-to-br from-blue-50 to-cyan-50 scale-105'
                  : 'border-slate-300 hover:border-slate-400 hover:bg-slate-50'
              }`}
                   onDragOver={handleDragOver}
                   onDragLeave={handleDragLeave}
                   onDrop={handleDrop}>
                <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-transparent rounded-2xl"></div>
                <div className="relative z-10">
                  <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center shadow-lg">
                    <ArrowUpTrayIcon className="h-10 w-10 text-white" />
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="file-upload" className="cursor-pointer">
                        <span className="text-xl font-semibold text-slate-800 hover:text-blue-600 transition-colors">
                          {file ? file.name : "Click to upload or drag and drop"}
                        </span>
                      </label>
                      <p className="text-slate-500 mt-2">
                        CSV, XLSX, XLS up to 10MB
                      </p>
                    </div>
                    <input
                      ref={fileInputRef}
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      className="sr-only"
                      onChange={handleFileChange}
                    />
                  </div>
                </div>
              </div>

              {/* Upload Button */}
              {file && !result && (
                <div className="mt-6 flex justify-center">
                  <button
                    onClick={handleUpload}
                    disabled={uploading || !auth.user?.id}
                    className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
                  >
                    {uploading ? (
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Uploading... {progress}%</span>
                      </div>
                    ) : !auth.user?.id ? (
                      <div className="flex items-center space-x-2">
                        <ArrowUpTrayIcon className="h-5 w-5" />
                        <span>Please Login to Upload</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <ArrowUpTrayIcon className="h-5 w-5" />
                        <span>Upload & Process</span>
                      </div>
                    )}
                  </button>
                </div>
              )}

            {file && (
              <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl">
                <div className="flex items-center space-x-3">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="font-semibold text-green-800">{file.name}</p>
                    <p className="text-sm text-green-600">
                      {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to upload
                    </p>
                  </div>
                  <button
                    onClick={() => setFile(null)}
                    className="ml-auto p-1 hover:bg-green-100 rounded-full transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5 text-green-600" />
                  </button>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-6 p-4 bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-xl">
                <div className="flex items-center space-x-3">
                  <XCircleIcon className="h-6 w-6 text-red-600" />
                  <div>
                    <p className="font-semibold text-red-800">Upload Failed</p>
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                  <button
                    onClick={() => setError("")}
                    className="ml-auto p-1 hover:bg-red-100 rounded-full transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5 text-red-600" />
                  </button>
                </div>
              </div>
            )}

            {result && (
              <div className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl">
                <div className="flex items-center space-x-3 mb-4">
                  <CheckCircleIcon className="h-8 w-8 text-blue-600" />
                  <div>
                    <h4 className="text-lg font-bold text-blue-800">Upload Successful!</h4>
                    <p className="text-blue-600">Your transactions have been processed</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-lg border border-blue-200">
                    <div className="text-2xl font-bold text-blue-600">{result.transactions_processed || 0}</div>
                    <div className="text-sm text-blue-800">Transactions Processed</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-green-200">
                    <div className="text-2xl font-bold text-green-600">{result.new_transactions || 0}</div>
                    <div className="text-sm text-green-800">New Transactions</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg border border-yellow-200">
                    <div className="text-2xl font-bold text-yellow-600">{result.duplicates_found || 0}</div>
                    <div className="text-sm text-yellow-800">Duplicates Found</div>
                  </div>
                </div>
              </div>
            )}
            </div>

            {/* Agent Status Widget for File Upload */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200 min-h-[600px] flex flex-col">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg">
                  <ArrowUpTrayIcon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-slate-900">File Upload Processing</h4>
                  <p className="text-sm text-slate-600">AI pipeline status for file uploads</p>
                </div>
              </div>
              <AgentStatusWidget agentStatus={uploadAgentStatus} />
            </div>
          </div>

          {/* Row 2: Chat + Agent Status */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* Conversational Transaction Entry */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200 min-h-[600px] flex flex-col">
              <ConversationalEntry
                onTransactionAdded={() => {}}
                updateAgentStatus={(status: Partial<AgentStatus>) => {
                  // Update chat agent status
                  setChatAgentStatus(prev => ({ ...prev, ...status }));
                }}
              />
            </div>

            {/* Agent Status Widget for Chat */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200 min-h-[600px] flex flex-col">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg">
                  <CheckCircleIcon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-slate-900">Chat Processing</h4>
                  <p className="text-sm text-slate-600">AI pipeline status for chat interactions</p>
                </div>
              </div>
              <AgentStatusWidget agentStatus={chatAgentStatus} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
