"""LangGraph workflow definition for the financial transaction processing pipeline"""

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..agents.ingestion_agent import IngestionAgent
from ..agents.ner_merchant_agent import NERMerchantAgent
from ..agents.classifier_agent import ClassifierAgent
from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent
from ..agents.suggestion_agent import SuggestionAgent
from ..agents.safety_guard_agent import SafetyGuardAgent
from ..schemas.transaction_schemas import RawTransaction


class TransactionProcessingState(TypedDict):
    """State object for the transaction processing workflow"""
    raw_transactions: List[Any]
    preprocessed_transactions: List[Any]
    merchant_transactions: List[Any]
    classified_transactions: List[Any]
    pattern_insights: List[Any]
    suggestions: List[Any]
    security_alerts: List[Any]
    current_step: str
    metadata: Dict[str, Any]


class TransactionWorkflow:
    """
    LangGraph workflow for processing financial transactions through 6 agents
    """
    
    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.ner_merchant_agent = NERMerchantAgent()
        self.classifier_agent = ClassifierAgent()
        self.pattern_analyzer_agent = PatternAnalyzerAgent()
        self.suggestion_agent = SuggestionAgent()
        self.safety_guard_agent = SafetyGuardAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(TransactionProcessingState)
        
        # Add nodes for each agent
        workflow.add_node("ingestion", self._ingestion_step)
        workflow.add_node("ner_merchant", self._ner_merchant_step)
        workflow.add_node("classifier", self._classifier_step)
        workflow.add_node("pattern_analyzer", self._pattern_analyzer_step)
        workflow.add_node("suggestion", self._suggestion_step)
        workflow.add_node("safety_guard", self._safety_guard_step)
        
        # Define the workflow edges (pipeline flow)
        workflow.add_edge("ingestion", "ner_merchant")
        workflow.add_edge("ner_merchant", "classifier")
        workflow.add_edge("classifier", "pattern_analyzer")
        workflow.add_edge("pattern_analyzer", "suggestion")
        workflow.add_edge("suggestion", "safety_guard")
        workflow.add_edge("safety_guard", END)
        
        # Set entry point
        workflow.set_entry_point("ingestion")
        
        return workflow
    
    def _ingestion_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 1: Process raw transactions through Ingestion Agent"""
        from ..agents.ingestion_agent import IngestionAgentInput
        
        # Create proper input model - convert RawTransaction objects to dicts if needed
        raw_data = []
        for t in state["raw_transactions"]:
            if hasattr(t, 'dict'):
                raw_data.append(t.dict())
            elif isinstance(t, dict):
                raw_data.append(t)
            else:
                raw_data.append(t.__dict__ if hasattr(t, '__dict__') else t)
        
        input_data = IngestionAgentInput(raw_transactions=raw_data)
        result = self.ingestion_agent.process(input_data)
        
        # Extract the actual data from the output model
        state["preprocessed_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.preprocessed_transactions]
        state["current_step"] = "ingestion_complete"
        return state

    def _ner_merchant_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 2: Extract merchant information through NER/Merchant Agent"""
        from ..agents.ner_merchant_agent import NERMerchantAgentInput
        from ..schemas.transaction_schemas import PreprocessedTransaction
        
        # Convert dict data back to PreprocessedTransaction objects
        preprocessed_txns = [PreprocessedTransaction(**t) if isinstance(t, dict) else t for t in state["preprocessed_transactions"]]
        input_data = NERMerchantAgentInput(preprocessed_transactions=preprocessed_txns)
        result = self.ner_merchant_agent.process(input_data)
        
        state["merchant_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.merchant_transactions]
        state["current_step"] = "ner_merchant_complete"
        return state

    def _classifier_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 3: Classify transactions through Classifier Agent"""
        from ..agents.classifier_agent import ClassifierAgentInput
        from ..schemas.transaction_schemas import MerchantTransaction
        
        # Convert dict data back to MerchantTransaction objects
        merchant_txns = [MerchantTransaction(**t) if isinstance(t, dict) else t for t in state["merchant_transactions"]]
        input_data = ClassifierAgentInput(merchant_transactions=merchant_txns)
        result = self.classifier_agent.process(input_data)
        
        state["classified_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.classified_transactions]
        state["current_step"] = "classifier_complete"
        return state

    def _pattern_analyzer_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 4: Analyze patterns through Pattern Analyzer Agent"""
        from ..agents.pattern_analyzer_agent import PatternAnalyzerAgentInput
        from ..schemas.transaction_schemas import ClassifiedTransaction
        
        # Convert dict data back to ClassifiedTransaction objects
        classified_txns = [ClassifiedTransaction(**t) if isinstance(t, dict) else t for t in state["classified_transactions"]]
        input_data = PatternAnalyzerAgentInput(
            classified_transactions=classified_txns,
            historical_data=[]  # Empty for now, could be populated from database
        )
        result = self.pattern_analyzer_agent.process(input_data)
        
        state["pattern_insights"] = [insight.dict() if hasattr(insight, 'dict') else insight for insight in result.pattern_insights]
        state["current_step"] = "pattern_analyzer_complete"
        return state

    def _suggestion_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 5: Generate suggestions through Suggestion Agent"""
        from ..agents.suggestion_agent import SuggestionAgentInput
        from ..schemas.transaction_schemas import PatternInsight
        
        # Convert dict data back to PatternInsight objects
        insights = [PatternInsight(**insight) if isinstance(insight, dict) else insight for insight in state["pattern_insights"]]
        input_data = SuggestionAgentInput(
            pattern_insights=insights,
            budget_thresholds={},  # Empty for now, could be from user settings
            user_preferences={}    # Empty for now, could be from user profile
        )
        result = self.suggestion_agent.process(input_data)
        
        state["suggestions"] = [s.dict() if hasattr(s, 'dict') else s for s in result.suggestions]
        state["current_step"] = "suggestion_complete"
        return state

    def _safety_guard_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 6: Safety check through Safety & Compliance Guard Agent"""
        from ..agents.safety_guard_agent import SafetyGuardAgentInput
        from ..schemas.transaction_schemas import ClassifiedTransaction
        
        # Convert dict data back to ClassifiedTransaction objects
        classified_txns = [ClassifiedTransaction(**t) if isinstance(t, dict) else t for t in state["classified_transactions"]]
        input_data = SafetyGuardAgentInput(classified_transactions=classified_txns, user_profile={})
        result = self.safety_guard_agent.process(input_data)
        
        state["security_alerts"] = [alert.dict() if hasattr(alert, 'dict') else alert for alert in result.security_alerts]
        state["current_step"] = "safety_guard_complete"
        return state

    def compile_workflow(self):
        """Compile the workflow with memory saver"""
        memory = MemorySaver()
        return self.workflow.compile(checkpointer=memory)
    
    async def process_transactions(self, raw_transactions: List[RawTransaction]) -> Dict[str, Any]:
        """Process transactions through the complete pipeline"""
        app = self.compile_workflow()
        
        initial_state = TransactionProcessingState(
            raw_transactions=raw_transactions,
            preprocessed_transactions=[],
            merchant_transactions=[],
            classified_transactions=[],
            pattern_insights=[],
            suggestions=[],
            security_alerts=[],
            current_step="starting",
            metadata={}
        )
        
        # Run the workflow
        final_state = await app.ainvoke(initial_state)
        
        return {
            "processed_transactions": final_state["classified_transactions"],
            "insights": final_state["pattern_insights"],
            "suggestions": final_state["suggestions"],
            "security_alerts": final_state["security_alerts"],
            "metadata": final_state["metadata"]
        }
