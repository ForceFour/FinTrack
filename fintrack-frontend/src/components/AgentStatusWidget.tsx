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
  idle: 'bg-gray-300 text-gray-700',
  running: 'bg-yellow-400 text-yellow-900',
  complete: 'bg-green-500 text-white',
  error: 'bg-red-500 text-white',
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
    <div className="bg-white rounded-lg shadow p-4">
        {Object.entries(agentStatus).map(([key, status]) => (
          <div
            key={key}
            className={`p-3 rounded-md ${statusColors[status as StatusType]} transition-all`}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {agentNames[key as keyof AgentStatus]}
              </span>
              <span className="text-lg">{(() => { const Icon = statusIcons[status as StatusType]; return <Icon />; })()}</span>
            </div>
            <div className="text-xs mt-1 capitalize">{status}</div>
          </div>
        ))}
      </div>
  );
}
