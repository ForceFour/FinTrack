'use client';

import { useApp } from '@/app/providers';
import { AgentStatus } from '@/lib/types';
import { PauseCircle, Zap, CheckCircle, XCircle } from "lucide-react";
import { LucideIcon } from 'lucide-react';

const agentNames: Record<keyof AgentStatus, string> = {
  ingestion: 'Ingestion',
  ner_merchant: 'NER/Merchant',
  classifier: 'Classifier',
  pattern_analyzer: 'Pattern Analyzer',
  suggestion: 'Suggestion',
  safety_guard: 'Safety Guard',
};

type StatusType = 'idle' | 'running' | 'complete' | 'error';

const statusColors: Record<StatusType, string> = {
  idle: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 border-gray-300',
  running: 'bg-gradient-to-r from-yellow-400 to-orange-400 text-yellow-900 border-yellow-500',
  complete: 'bg-gradient-to-r from-green-500 to-emerald-500 text-white border-green-600',
  error: 'bg-gradient-to-r from-red-500 to-red-600 text-white border-red-600',
};

const statusIcons: Record<StatusType, LucideIcon> = {
  idle: PauseCircle,
  running: Zap,
  complete: CheckCircle,
  error: XCircle,
};


export default function AgentStatusWidget() {
  const { agentStatus } = useApp();

  return (
    <div className="bg-gradient-to-br from-white via-gray-50 to-blue-50 rounded-xl shadow-xl border border-gray-200/50 backdrop-blur-sm p-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-gray-900">AI Processing Pipeline</h3>
          <p className="text-sm text-gray-600">Real-time status of transaction processing agents</p>
        </div>
      </div>

      <div className="space-y-3">
        {Object.entries(agentStatus).map(([key, status]) => (
          <div
            key={key}
            className={`p-4 rounded-xl border-2 shadow-sm transition-all duration-300 hover:shadow-md ${
              statusColors[status as StatusType]
            } ${status === 'running' ? 'animate-pulse' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  status === 'running' ? 'bg-white/20' :
                  status === 'complete' ? 'bg-white/30' :
                  status === 'error' ? 'bg-white/20' : 'bg-gray-200/50'
                }`}>
                  {(() => { const Icon = statusIcons[status as StatusType]; return <Icon className="h-4 w-4" />; })()}
                </div>
                <div>
                  <span className="text-sm font-semibold block">
                    {agentNames[key as keyof AgentStatus]}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    status === 'running' ? 'bg-white/30 text-yellow-100' :
                    status === 'complete' ? 'bg-white/40 text-green-100' :
                    status === 'error' ? 'bg-white/30 text-red-100' : 'bg-gray-300/50 text-gray-600'
                  }`}>
                    {status}
                  </span>
                </div>
              </div>
              {status === 'running' && (
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
