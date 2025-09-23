"""Agent modules for transaction processing pipeline"""

from .unified_classifier_agent import UnifiedClassifierAgent
from .ingestion_agent import IngestionAgent
from .ner_merchant_agent import NERMerchantAgent
from .pattern_analyzer_agent import PatternAnalyzerAgent
from .safety_guard_agent import SafetyGuardAgent
from .suggestion_agent import SuggestionAgent

# Backward compatibility aliases - all old agents now use the unified agent
ClassifierAgent = UnifiedClassifierAgent
TransactionClassifierAgent = UnifiedClassifierAgent

# Main exports - use UnifiedClassifierAgent for new implementations
__all__ = [
    'UnifiedClassifierAgent',
    'ClassifierAgent',  # Legacy alias
    'TransactionClassifierAgent',  # Legacy alias
    'IngestionAgent',
    'NERMerchantAgent',
    'PatternAnalyzerAgent',
    'SafetyGuardAgent',
    'SuggestionAgent'
]
