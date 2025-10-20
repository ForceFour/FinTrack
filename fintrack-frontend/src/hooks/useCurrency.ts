import { useState, useEffect } from "react";

export interface CurrencySettings {
  currency: string;
  symbol: string;
}

interface SpendingLimit {
  category: string;
  limit: number;
  period: "monthly" | "weekly";
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  LKR: "Rs.",
  USD: "$",
  EUR: "€",
  GBP: "£",
  INR: "₹",
};

const STORAGE_KEYS = {
  CURRENCY: "fintrack_currency_preference",
  SPENDING_LIMITS: "fintrack_spending_limits",
};

export const useCurrency = () => {
  const [currencySettings, setCurrencySettings] = useState<CurrencySettings>({
    currency: "LKR",
    symbol: "Rs.",
  });

  const [spendingLimits, setSpendingLimits] = useState<SpendingLimit[]>([]);

  // Load currency preference from local storage on mount
  useEffect(() => {
    const loadCurrencyPreference = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEYS.CURRENCY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setCurrencySettings(parsed);
        } else {
          // Set default to LKR if nothing is stored
          const defaultSettings = {
            currency: "LKR",
            symbol: "Rs.",
          };
          setCurrencySettings(defaultSettings);
          localStorage.setItem(
            STORAGE_KEYS.CURRENCY,
            JSON.stringify(defaultSettings)
          );
        }
      } catch (error) {
        console.error("Failed to load currency preference:", error);
        // Fallback to LKR on error
        setCurrencySettings({ currency: "LKR", symbol: "Rs." });
      }
    };

    const loadSpendingLimits = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEYS.SPENDING_LIMITS);
        if (stored) {
          const parsed = JSON.parse(stored);
          setSpendingLimits(parsed);
        }
      } catch (error) {
        console.error("Failed to load spending limits:", error);
      }
    };

    loadCurrencyPreference();
    loadSpendingLimits();
  }, []);

  const updateCurrency = (currency: string) => {
    const symbol = CURRENCY_SYMBOLS[currency] || currency;
    const newSettings = { currency, symbol };
    setCurrencySettings(newSettings);
    localStorage.setItem(STORAGE_KEYS.CURRENCY, JSON.stringify(newSettings));
  };

  const updateSpendingLimits = (limits: SpendingLimit[]) => {
    setSpendingLimits(limits);
    localStorage.setItem(STORAGE_KEYS.SPENDING_LIMITS, JSON.stringify(limits));
  };

  const formatAmount = (amount: number, includeSymbol: boolean = true): string => {
    const formatted = amount.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return includeSymbol ? `${currencySettings.symbol} ${formatted}` : formatted;
  };

  const formatAmountCompact = (amount: number, includeSymbol: boolean = true): string => {
    const abs = Math.abs(amount);
    let formatted: string;

    if (abs >= 1e9) {
      formatted = `${(abs / 1e9).toFixed(1)}B`;
    } else if (abs >= 1e6) {
      formatted = `${(abs / 1e6).toFixed(1)}M`;
    } else if (abs >= 1e3) {
      formatted = `${(abs / 1e3).toFixed(1)}K`;
    } else if (abs >= 100) {
      formatted = abs.toFixed(0);
    } else {
      formatted = abs.toFixed(2);
    }

    return includeSymbol
      ? `${currencySettings.symbol} ${formatted}`
      : formatted;
  };

  return {
    currency: currencySettings.currency,
    symbol: currencySettings.symbol,
    currencySettings,
    spendingLimits,
    updateCurrency,
    updateSpendingLimits,
    formatAmount,
    formatAmountCompact,
  };
};
