"""LangGraph workflow definition for the financial transaction processing pipeline"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver

from ..agents.ingestion_agent import IngestionAgent
from ..agents.ner_merchant_agent import NERMerchantAgent
from ..agents.classifier_agent import ClassifierAgent
from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent
from ..agents.suggestion_agent import SuggestionAgent
from ..agents.safety_guard_agent import SafetyGuardAgent
from ..schemas.transaction_schemas import RawTransaction


class TransactionProcessingState(Dict[str, Any]):
    """State object for the transaction processing workflow"""
    raw_transactions: List[RawTransaction]
    preprocessed_transactions: List[Dict[str, Any]]
    merchant_transactions: List[Dict[str, Any]]
    classified_transactions: List[Dict[str, Any]]
    pattern_insights: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    security_alerts: List[Dict[str, Any]]
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
        result = self.ingestion_agent.process(state["raw_transactions"])
        state["preprocessed_transactions"] = result
        state["current_step"] = "ingestion_complete"
        return state
    
    def _ner_merchant_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 2: Extract merchant information through NER/Merchant Agent"""
        result = self.ner_merchant_agent.process(state["preprocessed_transactions"])
        state["merchant_transactions"] = result
        state["current_step"] = "ner_merchant_complete"
        return state
    
    def _classifier_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 3: Classify transactions through Classifier Agent"""
        result = self.classifier_agent.process(state["merchant_transactions"])
        state["classified_transactions"] = result
        state["current_step"] = "classifier_complete"
        return state
    
    def _pattern_analyzer_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 4: Analyze patterns through Pattern Analyzer Agent"""
        result = self.pattern_analyzer_agent.process(state["classified_transactions"])
        state["pattern_insights"] = result
        state["current_step"] = "pattern_analyzer_complete"
        return state
    
    def _suggestion_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 5: Generate suggestions through Suggestion Agent"""
        result = self.suggestion_agent.process(state["pattern_insights"])
        state["suggestions"] = result
        state["current_step"] = "suggestion_complete"
        return state
    
    def _safety_guard_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 6: Safety check through Safety & Compliance Guard Agent"""
        result = self.safety_guard_agent.process(state["classified_transactions"])
        state["security_alerts"] = result
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
