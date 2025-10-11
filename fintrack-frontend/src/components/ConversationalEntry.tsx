"use client";

import { useState, useRef, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { ConversationMessage, ConversationContext } from "@/lib/types";
import { SendIcon, MessageCircleIcon, BotIcon, UserIcon, RefreshCwIcon } from "lucide-react";
import { useApp } from "@/app/providers";

interface ConversationalEntryProps {
  onTransactionAdded?: () => void;
}

export default function ConversationalEntry({ onTransactionAdded }: ConversationalEntryProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationContext, setConversationContext] = useState<ConversationContext>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { refreshTransactions } = useApp();

  // Check if we have a pending transaction that needs more info
  const contextData = conversationContext as { pending_transaction?: unknown; missing_fields?: unknown };
  const hasPendingTransaction = !!contextData.pending_transaction;
  const missingFields = (contextData.missing_fields as string[]) || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: ConversationMessage = {
      type: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const response = await apiClient.processNaturalLanguageTransaction(
        userMessage.content,
        conversationContext
      );

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

        setMessages(prev => [...prev, assistantMessage]);

        // Update conversation context if provided
        if (data.conversation_context) {
          setConversationContext(data.conversation_context);
        }

        // Handle different response types
        if (data.status === "completed" && data.transaction_processed) {
          // Transaction was successfully created
          refreshTransactions();

          // Add a follow-up message with next steps
          const nextStepsMessage: ConversationMessage = {
            type: "assistant",
            content: `🎉 Transaction saved! ${data.next_action || "You can view it in your Dashboard or continue adding more transactions."}`,
            timestamp: new Date().toISOString(),
          };
          setMessages(prev => [...prev, nextStepsMessage]);

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
          content: response.error || "Sorry, I couldn't process your request. Please try again.",
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch {
      const errorMessage: ConversationMessage = {
        type: "assistant",
        content: "Sorry, I encountered an error. Please try again or use the file upload option.",
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
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
    "Coffee shop $4.75 this morning"
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center space-x-2">
          <MessageCircleIcon className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Conversational Transaction Entry</h3>
        </div>
        <p className="text-sm text-gray-600 mt-1">
          Enter transaction details by typing them naturally - I&apos;ll understand and process them for you!
        </p>
        {hasPendingTransaction && missingFields.length > 0 && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">Missing information:</span> {missingFields.join(", ")}
            </p>
          </div>
        )}
        {hasPendingTransaction && missingFields.length === 0 && (
          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">
              ✅ Ready to save transaction
            </p>
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <BotIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">Start a conversation!</h4>
            <p className="text-gray-600 mb-4">Try saying something like:</p>
            <div className="space-y-2">
              {exampleMessages.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setInput(example)}
                  className="block w-full text-left p-2 bg-gray-50 hover:bg-gray-100 rounded-md text-sm text-gray-700 transition-colors"
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
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-900"
              }`}
            >
              <div className="flex items-center space-x-2 mb-1">
                {message.type === "user" ? (
                  <UserIcon className="h-4 w-4" />
                ) : (
                  <BotIcon className="h-4 w-4" />
                )}
                <span className="text-xs opacity-75">
                  {message.type === "user" ? "You" : "AI Assistant"}
                </span>
              </div>
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <BotIcon className="h-4 w-4" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex space-x-2">
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
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isTyping}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isTyping}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isTyping ? (
              <RefreshCwIcon className="h-4 w-4 animate-spin" />
            ) : (
              <SendIcon className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Conversation Stats */}
        {messages.length > 0 && (
          <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
            <span>{messages.length} messages</span>
            <div className="flex space-x-3">
              <button
                onClick={() => setConversationContext({})}
                className="text-green-600 hover:text-green-800 transition-colors"
              >
                New Transaction
              </button>
              <button
                onClick={clearConversation}
                className="text-blue-600 hover:text-blue-800 transition-colors"
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
