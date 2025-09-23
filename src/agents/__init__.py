"""Agent modules for transaction processing pipeline"""

from .classifier_agent import ClassifierAgent
from .ingestion_agent import IngestionAgent
from .ner_merchant_agent import NERMerchantAgent
from .pattern_analyzer_agent import PatternAnalyzerAgent
from .safety_guard_agent import SafetyGuardAgent
from .suggestion_agent import SuggestionAgent

# Backward compatibility aliases - all old agents now use the classifier agent
UnifiedClassifierAgent = ClassifierAgent  # Legacy alias
TransactionClassifierAgent = ClassifierAgent  # Legacy alias

# Main exports - use ClassifierAgent for new implementations
__all__ = [
    'ClassifierAgent',
    'UnifiedClassifierAgent',  # Legacy alias
    'TransactionClassifierAgent',  # Legacy alias
    'IngestionAgent',
    'NERMerchantAgent',
    'PatternAnalyzerAgent',
    'SafetyGuardAgent',
    'SuggestionAgent'
]
