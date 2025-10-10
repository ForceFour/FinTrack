"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { AuthState, AgentStatus } from "@/lib/types";
import { signIn, signOut, onAuthStateChange } from "@/lib/auth";

interface AppContextType {
  auth: AuthState;
  agentStatus: AgentStatus;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  updateAgentStatus: (status: Partial<AgentStatus>) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function Providers({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const [agentStatus, setAgentStatus] = useState<AgentStatus>({
    ingestion: "idle",
    ner_merchant: "idle",
    classifier: "idle",
    pattern_analyzer: "idle",
    suggestion: "idle",
    safety_guard: "idle",
  });

  useEffect(() => {
    // Listen to auth state changes
    const { data: { subscription } } = onAuthStateChange((user) => {
      if (user) {
        setAuth({
          user: {
            id: user.id,
            username: user.user_metadata?.username || user.email || '',
            email: user.email || '',
            full_name: user.user_metadata?.full_name || '',
          },
          token: null, // Supabase handles tokens internally
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        setAuth({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (
    email: string,
    password: string
  ): Promise<boolean> => {
    try {
      const response = await signIn({ email, password });
      if (response.error) {
        throw new Error(response.error);
      }
      // Auth state will be updated via onAuthStateChange listener
      return true;
    } catch (error) {
      console.error("Login error:", error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await signOut();
      // Auth state will be updated via onAuthStateChange listener
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  const updateAgentStatus = (status: Partial<AgentStatus>) => {
    setAgentStatus((prev) => ({ ...prev, ...status }));
  };

  return (
    <AppContext.Provider
      value={{ auth, agentStatus, login, logout, updateAgentStatus }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within Providers");
  }
  return context;
}
