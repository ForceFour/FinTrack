"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { AuthState, AgentStatus } from "@/lib/types";
import { apiClient } from "@/lib/api-client";

interface AppContextType {
  auth: AuthState;
  agentStatus: AgentStatus;
  login: (username: string, password: string) => Promise<boolean>;
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
    // Check for existing token on mount
    const token = localStorage.getItem("access_token");
    if (token) {
      apiClient.setToken(token);
      // Verify token and get user profile
      apiClient.getUserProfile().then((response) => {
        if (response.status === "success" && response.data) {
          setAuth({
            user: response.data,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } else {
          // Token invalid, clear it
          localStorage.removeItem("access_token");
          setAuth({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      });
    } else {
      setAuth((prev) => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = async (
    username: string,
    password: string
  ): Promise<boolean> => {
    const response = await apiClient.login(username, password);

    if (response.status === "success" && response.data) {
      setAuth({
        user: response.data.user,
        token: response.data.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
      return true;
    }

    return false;
  };

  const logout = () => {
    apiClient.logout();
    setAuth({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
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
