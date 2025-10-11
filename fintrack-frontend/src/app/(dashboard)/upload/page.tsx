"use client";

import { useState, useRef, ChangeEvent } from "react";
import { useApp } from "@/app/providers";
import { apiClient } from "@/lib/api-client";
import {
  ArrowUpTrayIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import AgentStatusWidget from "@/components/AgentStatusWidget";
import ConversationalEntry from "@/components/ConversationalEntry";

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
  const { updateAgentStatus, refreshTransactions } = useApp();

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

    // Start agents
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    // Update agent status
    for (let i = 0; i < agents.length; i++) {
      updateAgentStatus({ [agents[i]]: "running" });
      await new Promise((resolve) => setTimeout(resolve, 800));
      updateAgentStatus({ [agents[i]]: "complete" });
    }

    try {
      // Create a new File object to avoid reference issues
      const fileToUpload = new File([file], file.name, { type: file.type });

      // Upload file to backend API for AI processing
      const response = await apiClient.uploadTransactions(fileToUpload);

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
      agents.forEach((agent) => updateAgentStatus({ [agent]: "error" }));
    } finally {
      clearInterval(progressInterval);
      setUploading(false);

      // Reset agents to idle after a delay
      setTimeout(() => {
        agents.forEach((agent) => updateAgentStatus({ [agent]: "idle" }));
      }, 3000);
    }
  };

  const resetForm = () => {
    setFile(null);
    setResult(null);
    setError("");
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Upload & Process Transactions
        </h1>
        <p className="text-gray-600 mt-2">
          AI-Powered Transaction Processing & Analysis
        </p>
      </div>

      {/* Agent Status */}
      <AgentStatusWidget />

      {/* File Upload Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Upload Transaction File</h3>

        <div className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}`}
             onDragOver={handleDragOver}
             onDragLeave={handleDragLeave}
             onDrop={handleDrop}>
          <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
          <div className="mt-4">
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="mt-2 block text-sm font-medium text-gray-900">
                {file ? file.name : "Click to upload or drag and drop"}
              </span>
              <span className="mt-1 block text-xs text-gray-500">
                CSV, XLSX, XLS up to 10MB
              </span>
              <input
                ref={fileInputRef}
                id="file-upload"
                name="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls"
                className="sr-only"
                onChange={handleFileChange}
              />
            </label>
          </div>
        </div>

        {file && !result && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <CheckCircleIcon className="h-6 w-6 text-green-500" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? "Processing..." : "Start Processing"}
              </button>
            </div>

            {uploading && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Processing...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Running AI agents: Ingestion → NER/Merchant → Classifier →
                  Pattern Analyzer → Suggestion → Safety Guard
                </p>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-4 bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
            <div className="flex items-center">
              <XCircleIcon className="h-5 w-5 mr-2" />
              {error}
            </div>
          </div>
        )}

        {result && (
          <div className="mt-4 bg-green-50 border border-green-400 text-green-700 px-4 py-3 rounded">
            <div className="flex items-center mb-2">
              <CheckCircleIcon className="h-5 w-5 mr-2" />
              <span className="font-semibold">Processing Complete!</span>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div>
                <p className="text-sm text-gray-600">Transactions Processed</p>
                <p className="text-2xl font-bold">
                  {result.transactions_processed || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">New Transactions</p>
                <p className="text-2xl font-bold">
                  {result.new_transactions || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Duplicates Found</p>
                <p className="text-2xl font-bold">
                  {result.duplicates_found || 0}
                </p>
              </div>
            </div>
            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => (window.location.href = "/dashboard")}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                View Dashboard
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              >
                Upload Another File
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Processing Options */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">AI Processing Options</h3>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="form-checkbox h-5 w-5 text-indigo-600 rounded"
            />
            <div>
              <p className="font-medium text-gray-900">AI Categorization</p>
              <p className="text-sm text-gray-500">
                Use LLM for transaction categorization
              </p>
            </div>
          </label>
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="form-checkbox h-5 w-5 text-indigo-600 rounded"
            />
            <div>
              <p className="font-medium text-gray-900">ML Classification</p>
              <p className="text-sm text-gray-500">
                Enable machine learning classification
              </p>
            </div>
          </label>
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="form-checkbox h-5 w-5 text-indigo-600 rounded"
            />
            <div>
              <p className="font-medium text-gray-900">Security Scan</p>
              <p className="text-sm text-gray-500">
                Run fraud detection and security checks
              </p>
            </div>
          </label>
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="form-checkbox h-5 w-5 text-indigo-600 rounded"
            />
            <div>
              <p className="font-medium text-gray-900">Generate Suggestions</p>
              <p className="text-sm text-gray-500">
                AI-powered financial recommendations
              </p>
            </div>
          </label>
        </div>
      </div>

      {/* Expected File Format */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Expected File Format</h3>
        <div className="bg-gray-50 p-4 rounded-md font-mono text-sm">
          <p className="font-semibold mb-2">CSV Format:</p>
          <pre className="text-xs overflow-x-auto">
            {`date,amount,description,payment_method,account_type
2024-01-15,-45.67,"STARBUCKS STORE #12345","Credit Card","Checking"
2024-01-16,-123.45,"WALMART SUPERCENTER #5678","Debit Card","Checking"`}
          </pre>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          <p className="font-semibold mb-2">Required columns:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>date: Transaction date (YYYY-MM-DD format)</li>
            <li>
              amount: Transaction amount (negative for expenses, positive for
              income)
            </li>
            <li>description: Transaction description or memo</li>
          </ul>
          <p className="font-semibold mt-4 mb-2">Optional columns:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>category: Transaction category</li>
            <li>merchant: Merchant or payee name</li>
            <li>payment_method: Payment method used</li>
          </ul>
        </div>
      </div>

      {/* Conversational Transaction Entry */}
      <div className="bg-white p-6 rounded-lg shadow">
        <ConversationalEntry onTransactionAdded={() => {
          // Refresh data or show success message
          console.log("Transaction added via conversation");
        }} />
      </div>
    </div>
  );
}
