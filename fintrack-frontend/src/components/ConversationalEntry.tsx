"use client";

import { useState, useRef, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { ConversationMessage, ConversationContext } from "@/lib/types";
import {
  SendIcon,
  MessageCircleIcon,
  BotIcon,
  UserIcon,
  RefreshCwIcon,
  CheckCircle,
} from "lucide-react";
import { useApp } from "@/app/providers";

interface ConversationalEntryProps {
  onTransactionAdded?: () => void;
}

export default function ConversationalEntry({
  onTransactionAdded,
}: ConversationalEntryProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationContext, setConversationContext] =
    useState<ConversationContext>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const isInitialMount = useRef(true);
  const { refreshTransactions, auth, updateAgentStatus } = useApp();

  // Check if we have a pending transaction that needs more info
  const contextData = conversationContext as {
    pending_transaction?: unknown;
    missing_fields?: unknown;
  };
  const hasPendingTransaction = !!contextData.pending_transaction;
  const missingFields = (contextData.missing_fields as string[]) || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
            content: `🎉 Transaction saved! ${
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
    "I spent $25 at Starbucks yesterday",
    "Paid $120 for groceries at Walmart today using my credit card",
    "Gas station charge of $45.50 on Monday",
    "Coffee shop $4.75 this morning",
  ];

  return (
    <div className="bg-gradient-to-br from-white via-blue-50 to-indigo-50 rounded-xl shadow-xl border border-gray-200/50 backdrop-blur-sm">
      {/* Header */}
      <div className="p-6 border-b border-gray-200/50 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 rounded-t-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <MessageCircleIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">
              Conversational Transaction Entry
            </h3>
            <p className="text-sm text-blue-100 mt-1">
              Enter transaction details naturally - I&apos;ll understand and
              process them for you!
            </p>
          </div>
        </div>
        {hasPendingTransaction && missingFields.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-400/20 border border-yellow-300/30 rounded-lg backdrop-blur-sm">
            <p className="text-sm text-yellow-100">
              <span className="font-semibold">Missing information:</span>{" "}
              {missingFields.join(", ")}
            </p>
          </div>
        )}
        {hasPendingTransaction && missingFields.length === 0 && (
          <div className="mt-4 p-3 bg-green-400/20 border border-green-300/30 rounded-lg backdrop-blur-sm">
            <p className="text-sm text-green-100 flex items-center space-x-2">
              <CheckCircle className="h-4 w-4" />
              <span>Ready to save transaction</span>
            </p>
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-transparent to-gray-50/30">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="p-4 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <BotIcon className="h-10 w-10 text-blue-600" />
            </div>
            <h4 className="text-xl font-bold text-gray-900 mb-3">
              Start a conversation!
            </h4>
            <p className="text-gray-600 mb-6">Try saying something like:</p>
            <div className="space-y-3 max-w-md mx-auto">
              {exampleMessages.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setInput(example)}
                  className="block w-full text-left p-4 bg-white hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 border border-gray-200 hover:border-blue-300 rounded-xl text-sm text-gray-700 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  &ldquo;{example}&rdquo;
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
              className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm ${
                message.type === "user"
                  ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-md"
                  : "bg-white text-gray-900 border border-gray-200 rounded-bl-md"
              }`}
            >
              <div className="flex items-center space-x-2 mb-2">
                {message.type === "user" ? (
                  <UserIcon className="h-4 w-4 opacity-90" />
                ) : (
                  <BotIcon className="h-4 w-4 text-blue-600" />
                )}
                <span
                  className={`text-xs font-medium ${
                    message.type === "user" ? "text-blue-100" : "text-gray-500"
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
            <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md border border-gray-200 shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="p-1 bg-blue-100 rounded-full">
                  <BotIcon className="h-4 w-4 text-blue-600" />
                </div>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                </div>
                <span className="text-xs text-gray-500 font-medium">
                  AI is thinking...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-gray-200/50 bg-gradient-to-r from-gray-50 to-blue-50/30 rounded-b-xl">
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
                  : "Type your transaction here... (e.g., 'I spent $25 at Starbucks yesterday')"
              }
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm transition-all duration-200"
              disabled={isTyping}
            />
            {input.trim() && (
              <button
                onClick={() => setInput("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                ×
              </button>
            )}
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isTyping}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            {isTyping ? (
              <RefreshCwIcon className="h-5 w-5 animate-spin" />
            ) : (
              <SendIcon className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Conversation Stats */}
        {messages.length > 0 && (
          <div className="flex justify-between items-center mt-4 text-sm">
            <span className="text-gray-500 bg-white px-3 py-1 rounded-full border border-gray-200">
              {messages.length} messages
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setConversationContext({})}
                className="px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
              >
                New Transaction
              </button>
              <button
                onClick={clearConversation}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
              >
                Clear conversation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
