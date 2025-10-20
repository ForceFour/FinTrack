"use client";


import { useState, useRef, ChangeEvent } from "react";
import { useApp } from "@/app/providers";
import { apiClient } from "@/lib/api-client";
import {
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
  XMarkIcon,
  SparklesIcon,
  DocumentArrowUpIcon,
  ChatBubbleLeftRightIcon,
  BoltIcon,
  ShieldCheckIcon,
  ClockIcon,
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Hero Header Section */}
        <div className="relative bg-white rounded-3xl shadow-2xl p-6 md:p-8 lg:p-10 border border-slate-200 overflow-hidden">
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-pink-400/20 to-orange-400/20 rounded-full blur-3xl -ml-24 -mb-24"></div>

          <div className="relative z-10">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="relative">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur-lg opacity-50 animate-pulse"></div>
                    <div className="relative p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg">
                      <SparklesIcon className="w-8 h-8 text-white" />
                    </div>
                  </div>
                  <div>
                    <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                      Smart Transaction Upload
                    </h1>
                  </div>
                </div>
                <p className="text-slate-600 text-base md:text-lg leading-relaxed max-w-3xl">
                  Upload your financial data and let our AI-powered agents analyze, categorize, and provide actionable insights in real-time.
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <div className="flex items-center space-x-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-full shadow-lg">
                  <ShieldCheckIcon className="w-5 h-5" />
                  <span className="text-sm font-medium">Secure & Encrypted</span>
                </div>
                <div className="flex items-center space-x-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-4 py-2 rounded-full shadow-lg">
                  <BoltIcon className="w-5 h-5" />
                  <span className="text-sm font-medium">Lightning Fast</span>
                </div>
              </div>
            </div>

            {/* Quick Stats Bar */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center space-x-3 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-200">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <DocumentArrowUpIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">CSV & Excel</div>
                  <div className="text-sm text-blue-800">Supported Formats</div>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
                <div className="p-2 bg-purple-500 rounded-lg">
                  <ChatBubbleLeftRightIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600">AI Chat</div>
                  <div className="text-sm text-purple-800">Conversational Entry</div>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                <div className="p-2 bg-green-500 rounded-lg">
                  <ClockIcon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">&lt;30s</div>
                  <div className="text-sm text-green-800">Processing Time</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Two Column Layout */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Left Column: File Upload + Agent Status */}
          <div className="space-y-6">
            {/* File Upload Card */}
            <div className="bg-white rounded-3xl shadow-xl p-6 md:p-8 border border-slate-200 hover:shadow-2xl transition-all duration-300">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-lg">
                    <DocumentArrowUpIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-800">File Upload</h3>
                    <p className="text-sm text-slate-500">Drag & drop or click to upload</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${uploading ? 'bg-orange-500 animate-pulse' : 'bg-green-500'}`}></div>
                  <span className="text-xs font-medium text-slate-600">{uploading ? 'Processing' : 'Ready'}</span>
                </div>
              </div>

              {/* Drop Zone */}
              <div
                className={`relative border-2 border-dashed rounded-2xl p-8 md:p-12 text-center transition-all duration-300 ${
                  isDragOver
                    ? 'border-blue-500 bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 scale-[1.02] shadow-xl'
                    : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {!file ? (
                  <div className="space-y-4">
                    <div className="relative w-24 h-24 mx-auto">
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full blur-2xl opacity-40 animate-pulse"></div>
                      <div className="relative w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-2xl transform hover:scale-110 transition-transform">
                        <ArrowUpTrayIcon className="h-12 w-12 text-white" />
                      </div>
                    </div>

                    <div>
                      <label htmlFor="file-upload" className="cursor-pointer">
                        <span className="text-xl font-bold text-slate-800 hover:text-blue-600 transition-colors block">
                          Drop your file here
                        </span>
                        <span className="text-slate-500 mt-2 block">or click to browse</span>
                      </label>
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

                    <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
                      <span className="px-3 py-1 bg-slate-100 rounded-full">CSV</span>
                      <span className="px-3 py-1 bg-slate-100 rounded-full">XLSX</span>
                      <span className="px-3 py-1 bg-slate-100 rounded-full">XLS</span>
                    </div>

                    <p className="text-xs text-slate-400">Maximum file size: 10MB</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="relative w-20 h-20 mx-auto">
                      <CheckCircleIcon className="w-20 h-20 text-green-500" />
                    </div>
                    <div>
                      <p className="text-lg font-bold text-slate-800">{file.name}</p>
                      <p className="text-sm text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                    <button
                      onClick={() => setFile(null)}
                      className="text-sm text-red-600 hover:text-red-700 font-medium"
                    >
                      Remove file
                    </button>
                  </div>
                )}
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div className="mt-6 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600 font-medium">Processing...</span>
                    <span className="text-blue-600 font-bold">{progress}%</span>
                  </div>
                  <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-500 rounded-full relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                    </div>
                  </div>
                </div>
              )}

              {/* Upload Button */}
              {file && !result && !uploading && (
                <div className="mt-6">
                  <button
                    onClick={handleUpload}
                    disabled={!auth.user?.id}
                    className="w-full px-8 py-4 bg-gradient-to-r from-blue-500 via-purple-600 to-pink-500 text-white font-bold rounded-2xl hover:from-blue-600 hover:via-purple-700 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-2xl hover:shadow-3xl transform hover:scale-[1.02] relative overflow-hidden group"
                  >
                    <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                    <div className="relative flex items-center justify-center space-x-3">
                      {!auth.user?.id ? (
                        <>
                          <XCircleIcon className="h-6 w-6" />
                          <span>Please Login to Upload</span>
                        </>
                      ) : (
                        <>
                          <SparklesIcon className="h-6 w-6" />
                          <span>Process with AI</span>
                          <BoltIcon className="h-6 w-6" />
                        </>
                      )}
                    </div>
                  </button>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="mt-6 p-4 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-200 rounded-2xl">
                  <div className="flex items-start space-x-3">
                    <XCircleIcon className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold text-red-800 text-sm">Upload Failed</p>
                      <p className="text-sm text-red-600 mt-1">{error}</p>
                    </div>
                    <button
                      onClick={() => setError("")}
                      className="p-1 hover:bg-red-100 rounded-full transition-colors"
                    >
                      <XMarkIcon className="h-5 w-5 text-red-600" />
                    </button>
                  </div>
                </div>
              )}

              {/* Success Result */}
              {result && (
                <div className="mt-6 p-6 bg-gradient-to-r from-green-50 via-emerald-50 to-teal-50 border-2 border-green-200 rounded-2xl">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="p-2 bg-green-500 rounded-xl">
                      <CheckCircleIcon className="h-8 w-8 text-white" />
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-green-800">Processing Complete! 🎉</h4>
                      <p className="text-sm text-green-600">Your transactions have been analyzed</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-white p-4 rounded-xl border-2 border-blue-200 text-center">
                      <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                        {result.transactions_processed || 0}
                      </div>
                      <div className="text-xs text-slate-600 mt-1 font-medium">Processed</div>
                    </div>
                    <div className="bg-white p-4 rounded-xl border-2 border-green-200 text-center">
                      <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                        {result.new_transactions || 0}
                      </div>
                      <div className="text-xs text-slate-600 mt-1 font-medium">New</div>
                    </div>
                    <div className="bg-white p-4 rounded-xl border-2 border-yellow-200 text-center">
                      <div className="text-3xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">
                        {result.duplicates_found || 0}
                      </div>
                      <div className="text-xs text-slate-600 mt-1 font-medium">Duplicates</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Agent Status for Upload */}
            <div className="bg-white rounded-3xl shadow-xl p-6 md:p-8 border border-slate-200">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg">
                  <BoltIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-slate-900">AI Processing Pipeline</h4>
                  <p className="text-sm text-slate-500">Real-time agent status for file upload</p>
                </div>
              </div>
              <AgentStatusWidget agentStatus={uploadAgentStatus} />
            </div>
          </div>

          {/* Right Column: Chat + Agent Status */}
          <div className="space-y-6">
            {/* Chat Interface Card */}
            <div className="bg-white rounded-3xl shadow-xl p-6 md:p-8 border border-slate-200 min-h-[600px] flex flex-col">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl shadow-lg">
                  <ChatBubbleLeftRightIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-800">AI Chat Entry</h3>
                  <p className="text-sm text-slate-500">Describe your transaction naturally</p>
                </div>
              </div>
              <ConversationalEntry
                onTransactionAdded={() => {}}
                updateAgentStatus={(status: Partial<AgentStatus>) => {
                  setChatAgentStatus(prev => ({ ...prev, ...status }));
                }}
              />
            </div>

            {/* Agent Status for Chat */}
            <div className="bg-white rounded-3xl shadow-xl p-6 md:p-8 border border-slate-200">
              <div className="flex items-center space-x-3 mb-6">
                <div className="p-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl shadow-lg">
                  <SparklesIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-slate-900">Chat AI Pipeline</h4>
                  <p className="text-sm text-slate-500">Real-time agent status for chat processing</p>
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
