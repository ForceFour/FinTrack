"use client";

import { useState, useRef, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { ConversationMessage, ConversationContext, AgentStatus } from "@/lib/types";
import {
  BotIcon,
  CheckCircle,
  MessageCircleIcon,
  RefreshCwIcon,
  SendIcon,
  UserIcon,
} from "lucide-react";
import { useApp } from "@/app/providers";
import { useCurrency } from "@/hooks/useCurrency";

interface ConversationalEntryProps {
  onTransactionAdded?: () => void;
  updateAgentStatus?: (status: Partial<AgentStatus>) => void;
}

export default function ConversationalEntry({
  onTransactionAdded,
  updateAgentStatus: propUpdateAgentStatus,
}: ConversationalEntryProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationContext, setConversationContext] =
    useState<ConversationContext>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const isInitialMount = useRef(true);
  const { refreshTransactions, auth, updateAgentStatus: globalUpdateAgentStatus } = useApp();
  const { symbol: currencySymbol } = useCurrency();

  // Use the passed updateAgentStatus or fall back to global
  const updateAgentStatus = propUpdateAgentStatus || globalUpdateAgentStatus;

  // Check if we have a pending transaction that needs more info
  const contextData = conversationContext as {
    pending_transaction?: unknown;
    missing_fields?: unknown;
  };
  const hasPendingTransaction = !!contextData.pending_transaction;
  const missingFields = (contextData.missing_fields as string[]) || [];

  const scrollToBottom = () => {
    const messagesContainer = messagesEndRef.current?.parentElement;
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  };

  useEffect(() => {
    // Only scroll to bottom if there are messages and it's not the initial mount
    if (messages.length > 0 && !isInitialMount.current) {
      scrollToBottom();
    }
    // Mark that initial mount is complete after first render
    if (isInitialMount.current) {
      isInitialMount.current = false;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: ConversationMessage = {
      type: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await apiClient.processNaturalLanguageTransaction(
        userMessage.content,
        conversationContext,
        auth.user?.id
      );

      // Simulate agent pipeline for conversational transactions
      const responseData = response.data as {
        status?: string;
        response?: string;
        conversation_context?: ConversationContext;
        transaction_processed?: boolean;
        transaction_ids?: string[];
        next_action?: string;
        needs_more_info?: boolean;
        missing_fields?: string[];
      };
      if (response.status === "success" && responseData?.status === "completed") {
        const agents = [
          "ingestion",
          "ner_merchant",
          "classifier",
          "pattern_analyzer",
          "suggestion",
          "safety_guard",
        ];

        // Update agent status sequentially to show pipeline progress
        for (let i = 0; i < agents.length; i++) {
          updateAgentStatus({ [agents[i]]: "running" });
          await new Promise((resolve) => setTimeout(resolve, 600));
          updateAgentStatus({ [agents[i]]: "complete" });
        }

        // Reset chat agents to idle after completion
        setTimeout(() => {
          updateAgentStatus({
            ingestion: "idle",
            ner_merchant: "idle",
            classifier: "idle",
            pattern_analyzer: "idle",
            suggestion: "idle",
            safety_guard: "idle",
          });
        }, 3000);
      }

      if (response.status === "success" && response.data) {
        const data = response.data as {
          response?: string;
          conversation_context?: ConversationContext;
          status?: string;
          transaction_processed?: boolean;
          transaction_id?: string;
          needs_more_info?: boolean;
          missing_fields?: string[];
          next_action?: string;
        };

        const assistantMessage: ConversationMessage = {
          type: "assistant",
          content: data.response || "Transaction processed successfully!",
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Update conversation context if provided
        if (data.conversation_context) {
          setConversationContext(data.conversation_context);
        }

        // Handle different response types
        if (data.status === "completed" && data.transaction_processed) {
          // Transaction was successfully created
          refreshTransactions();
          onTransactionAdded?.();

          // Add a follow-up message with next steps
          const nextStepsMessage: ConversationMessage = {
            type: "assistant",
            content: `Transaction saved! ${
              data.next_action ||
              "You can view it in your Dashboard or continue adding more transactions."
            }`,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, nextStepsMessage]);

          // Clear context for new transaction after a delay
          setTimeout(() => {
            setConversationContext({});
          }, 3000);
        } else if (data.status === "incomplete" || data.needs_more_info) {
          // More information needed, keep context for continuation
          // Context is already updated above
        } else if (data.status === "error") {
          // Error occurred, but we still show the response message
        }
      } else {
        const errorMessage: ConversationMessage = {
          type: "assistant",
          content:
            response.error ||
            "Sorry, I couldn't process your request. Please try again.",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch {
      const errorMessage: ConversationMessage = {
        type: "assistant",
        content:
          "Sorry, I encountered an error. Please try again or use the file upload option.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationContext({});
  };

  const exampleMessages = [
    `How much did I spend on food last month?`,
    `I spent ${currencySymbol} 2500 at Starbucks yesterday`,
    `Paid ${currencySymbol} 12000 for groceries at Walmart today`,
    `How much did I spend last week?`
  ];

  return (
    <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 p-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-white/20 rounded-xl backdrop-blur-sm shadow-lg">
            <MessageCircleIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              AI Transaction Assistant
            </h3>
            <p className="text-sm text-purple-100 mt-1">
              Ask questions about your spending or tell me about transactions - I&apos;ll help you manage your finances!
            </p>
          </div>
        </div>
        {hasPendingTransaction && missingFields.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-400/20 border border-yellow-300/30 rounded-xl backdrop-blur-sm">
            <p className="text-sm text-yellow-100 flex items-center space-x-2">
              <RefreshCwIcon className="h-4 w-4" />
              <span>
                <span className="font-semibold">Missing information:</span>{" "}
                {missingFields.join(", ")}
              </span>
            </p>
          </div>
        )}
        {hasPendingTransaction && missingFields.length === 0 && (
          <div className="mt-4 p-3 bg-green-400/20 border border-green-300/30 rounded-xl backdrop-blur-sm">
            <p className="text-sm text-green-100 flex items-center space-x-2">
              <CheckCircle className="h-4 w-4" />
              <span>Ready to save transaction</span>
            </p>
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="min-h-[400px] p-6 space-y-4 bg-gradient-to-b from-slate-50/50 to-white">
        {messages.length === 0 && (
          <div className="text-center py-2">
            <div className="p-2 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-2xl w-15 h-15 mx-auto mb-3 flex items-center justify-center shadow-lg">
              <BotIcon className="h-10 w-10 text-purple-600" />
            </div>
            <h4 className="text-xl font-bold text-slate-900 mb-3">
              Start a conversation!
            </h4>
            <p className="text-slate-600 mb-4 max-w-md mx-auto">
              Try saying something like:
            </p>
            <div className="space-y-1 max-w-md mx-auto">
              {exampleMessages.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setInput(example)}
                  className="block w-full text-left p-4 bg-white hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 border border-slate-200 hover:border-purple-300 rounded-2xl text-sm text-slate-700 transition-all duration-200 shadow-sm hover:shadow-lg transform hover:scale-[1.02]"
                >
                  &quot;{example}&quot;
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.type === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-5 py-3 rounded-2xl shadow-md ${
                message.type === "user"
                  ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-br-md"
                  : "bg-white text-slate-900 border border-slate-200 rounded-bl-md shadow-lg"
              }`}
            >
              <div className="flex items-center space-x-2 mb-2">
                {message.type === "user" ? (
                  <UserIcon className="h-4 w-4 opacity-90" />
                ) : (
                  <BotIcon className="h-4 w-4 text-purple-600" />
                )}
                <span
                  className={`text-xs font-semibold ${
                    message.type === "user" ? "text-purple-100" : "text-slate-500"
                  }`}
                >
                  {message.type === "user" ? "You" : "AI Assistant"}
                </span>
              </div>
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {message.content}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white px-5 py-3 rounded-2xl rounded-bl-md border border-slate-200 shadow-lg">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 bg-purple-100 rounded-full">
                  <BotIcon className="h-4 w-4 text-purple-600" />
                </div>
                <div className="flex space-x-1.5">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
                <span className="text-xs text-slate-500 font-semibold">
                  AI is thinking...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-slate-200 bg-gradient-to-r from-slate-50 to-purple-50/40">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                hasPendingTransaction && missingFields.length > 0
                  ? `Please provide: ${missingFields.join(", ")}`
                  : `Ask about spending or add transactions... (e.g., 'How much did I spend on food last month?' or 'I spent ${currencySymbol}25 at Starbucks today')`
              }
              className="w-full px-5 py-3.5 pr-12 border-2 border-slate-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white shadow-sm hover:shadow-md transition-all duration-200"
              disabled={isTyping}
            />
            {input.trim() && (
              <button
                onClick={() => setInput("")}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors text-xl font-bold"
              >
                ×
              </button>
            )}
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isTyping}
            className="px-7 py-3.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-2xl hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center space-x-2"
          >
            {isTyping ? (
              <RefreshCwIcon className="h-5 w-5 animate-spin" />
            ) : (
              <>
                <SendIcon className="h-5 w-5" />
                <span className="font-semibold">Send</span>
              </>
            )}
          </button>
        </div>

        {/* Conversation Stats */}
        {messages.length > 0 && (
          <div className="flex justify-between items-center mt-4 text-sm">
            <span className="text-slate-500 bg-white px-4 py-1.5 rounded-full border border-slate-200 font-medium shadow-sm">
              {messages.length} messages
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setConversationContext({})}
                className="px-4 py-1.5 bg-green-100 text-green-700 rounded-xl hover:bg-green-200 transition-colors text-sm font-semibold shadow-sm hover:shadow-md"
              >
                New Transaction
              </button>
              <button
                onClick={clearConversation}
                className="px-4 py-1.5 bg-purple-100 text-purple-700 rounded-xl hover:bg-purple-200 transition-colors text-sm font-semibold shadow-sm hover:shadow-md"
              >
                Clear Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
