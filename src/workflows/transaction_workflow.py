"""
Enhanced LangGraph Workflow for Transaction Processing Pipeline
Integrates: LangChain/Groq NL Processing + Enhanced Ingestion + NER + Classification
With LangSmith Tracing for Visualization
"""

import logging
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime
import os

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client

from ..states import TransactionProcessingState, ProcessingStage
from ..nodes import TransactionProcessingNodes
from ..nodes.specialized_nodes import ConditionalNodes, ErrorHandlingNodes, UtilityNodes

logger = logging.getLogger(__name__)

from ..agents.ingestion_agent import IngestionAgent
from ..agents.ner_merchant_agent import NERMerchantAgent
from ..agents.classifier_agent import ClassifierAgent
from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent
from ..agents.suggestion_agent import SuggestionAgent
from ..agents.safety_guard_agent import SafetyGuardAgent
from ..schemas.transaction_schemas import RawTransaction


class TransactionWorkflow:
    """
    LangGraph workflow for processing financial transactions through 6 agents
    With LangSmith tracing enabled for visualization
    """
    
    def __init__(self, enable_tracing: bool = True):
        # Initialize LangSmith client for tracing if enabled
        self.enable_tracing = enable_tracing
        if enable_tracing:
            self.langsmith_client = Client()
            logger.info("🎯 LangSmith tracing enabled for workflow visualization")
        
        self.ingestion_agent = IngestionAgent()
        self.ner_merchant_agent = NERMerchantAgent()
        self.classifier_agent = ClassifierAgent()
        self.pattern_analyzer_agent = PatternAnalyzerAgent()
        self.suggestion_agent = SuggestionAgent()
        self.safety_guard_agent = SafetyGuardAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with proper node names for visualization"""
        workflow = StateGraph(TransactionProcessingState)
        
        # Add nodes for each agent with descriptive names
        workflow.add_node("🚀 NL Processing & Ingestion", self._ingestion_step)
        workflow.add_node("🏷️ NER Merchant Extraction", self._ner_merchant_step) 
        workflow.add_node("📂 Transaction Classification", self._classifier_step)
        workflow.add_node("📊 Pattern Analysis", self._pattern_analyzer_step)
        workflow.add_node("💡 Smart Suggestions", self._suggestion_step)
        workflow.add_node("🛡️ Safety & Compliance", self._safety_guard_step)
        
        # Define the workflow edges (pipeline flow)
        workflow.add_edge("🚀 NL Processing & Ingestion", "🏷️ NER Merchant Extraction")
        workflow.add_edge("🏷️ NER Merchant Extraction", "📂 Transaction Classification")
        workflow.add_edge("📂 Transaction Classification", "📊 Pattern Analysis")
        workflow.add_edge("📊 Pattern Analysis", "💡 Smart Suggestions")
        workflow.add_edge("💡 Smart Suggestions", "🛡️ Safety & Compliance")
        workflow.add_edge("🛡️ Safety & Compliance", END)
        
        # Set entry point
        workflow.set_entry_point("🚀 NL Processing & Ingestion")
        
        return workflow
    
    def _ingestion_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 1: Process raw transactions through Ingestion Agent"""
        logger.info("🚀 INGESTION NODE: Starting transaction ingestion and preprocessing")
        
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
        
        logger.info(f"✅ INGESTION NODE: Processed {len(state['preprocessed_transactions'])} transactions")
        return state

    def _ner_merchant_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 2: Extract merchant information through NER/Merchant Agent"""
        logger.info("🏷️ NER NODE: Starting named entity recognition")
        
        from ..agents.ner_merchant_agent import NERMerchantAgentInput
        from ..schemas.transaction_schemas import PreprocessedTransaction
        
        # Convert dict data back to PreprocessedTransaction objects
        preprocessed_txns = [PreprocessedTransaction(**t) if isinstance(t, dict) else t for t in state["preprocessed_transactions"]]
        input_data = NERMerchantAgentInput(preprocessed_transactions=preprocessed_txns)
        result = self.ner_merchant_agent.process(input_data)
        
        state["merchant_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.merchant_transactions]
        state["current_step"] = "ner_merchant_complete"
        
        logger.info(f"✅ NER NODE: Extracted entities for {len(state['merchant_transactions'])} transactions")
        return state
        
        state["merchant_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.merchant_transactions]
        state["current_step"] = "ner_merchant_complete"
        return state

    def _classifier_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 3: Classify transactions through Classifier Agent"""
        logger.info("📂 CLASSIFICATION NODE: Starting transaction classification")
        
        from ..agents.classifier_agent import ClassifierAgentInput
        from ..schemas.transaction_schemas import MerchantTransaction
        
        # Convert dict data back to MerchantTransaction objects
        merchant_txns = [MerchantTransaction(**t) if isinstance(t, dict) else t for t in state["merchant_transactions"]]
        input_data = ClassifierAgentInput(merchant_transactions=merchant_txns)
        result = self.classifier_agent.process(input_data)
        
        state["classified_transactions"] = [t.dict() if hasattr(t, 'dict') else t for t in result.classified_transactions]
        state["current_step"] = "classifier_complete"
        
        logger.info(f"✅ CLASSIFICATION NODE: Classified {len(state['classified_transactions'])} transactions")
        return state

    def _pattern_analyzer_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 4: Analyze patterns through Pattern Analyzer Agent"""
        logger.info("📊 PATTERN NODE: Starting pattern analysis")
        
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
        
        logger.info(f"✅ PATTERN NODE: Generated {len(state['pattern_insights'])} insights")
        return state

    def _suggestion_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 5: Generate suggestions through Suggestion Agent"""
        logger.info("💡 SUGGESTION NODE: Starting smart suggestions generation")
        
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
        
        logger.info(f"✅ SUGGESTION NODE: Generated {len(state['suggestions'])} suggestions")
        return state

    def _safety_guard_step(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Step 6: Safety check through Safety & Compliance Guard Agent"""
        logger.info("🛡️ SAFETY NODE: Starting safety and compliance checks")
        
        from ..agents.safety_guard_agent import SafetyGuardAgentInput
        from ..schemas.transaction_schemas import ClassifiedTransaction
        
        # Convert dict data back to ClassifiedTransaction objects
        classified_txns = [ClassifiedTransaction(**t) if isinstance(t, dict) else t for t in state["classified_transactions"]]
        input_data = SafetyGuardAgentInput(classified_transactions=classified_txns, user_profile={})
        result = self.safety_guard_agent.process(input_data)
        
        state["security_alerts"] = [alert.dict() if hasattr(alert, 'dict') else alert for alert in result.security_alerts]
        state["current_step"] = "safety_guard_complete"
        
        logger.info(f"✅ SAFETY NODE: Generated {len(state['security_alerts'])} security alerts")
        return state

    def compile_workflow(self):
        """Compile the workflow with memory saver and tracing"""
        memory = MemorySaver()
        compiled_app = self.workflow.compile(checkpointer=memory)
        
        if self.enable_tracing:
            logger.info("🎯 LangSmith tracing configured for workflow visualization")
        
        return compiled_app
    
    async def process_transactions(self, raw_transactions: List[RawTransaction]) -> Dict[str, Any]:
        """Process transactions through the complete pipeline with LangSmith tracing"""
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

        # Run the workflow with proper configuration including tracing
        config = {
            "configurable": {
                "thread_id": f"fintrack_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        if self.enable_tracing:
            logger.info("🚀 Starting workflow execution with LangSmith tracing")
            logger.info("📊 Visit https://smith.langchain.com to view workflow visualization")
        
        # Run the workflow
        final_state = await app.ainvoke(initial_state, config=config)
        
        return {
            "processed_transactions": final_state["classified_transactions"],
            "insights": final_state["pattern_insights"],
            "suggestions": final_state["suggestions"],
            "security_alerts": final_state["security_alerts"],
            "metadata": final_state["metadata"]
        }
    
    async def process_preprocessed_transactions(self, preprocessed_transactions: List[Any]) -> Dict[str, Any]:
        """Process already preprocessed transactions starting from NER step"""
        # Create a workflow that starts from NER merchant step
        workflow = StateGraph(TransactionProcessingState)
        
        # Add nodes (skip ingestion)
        workflow.add_node("ner_merchant", self._ner_merchant_step)
        workflow.add_node("classifier", self._classifier_step)
        workflow.add_node("pattern_analyzer", self._pattern_analyzer_step)
        workflow.add_node("suggestion", self._suggestion_step)
        workflow.add_node("safety_guard", self._safety_guard_step)
        
        # Define edges starting from NER
        workflow.add_edge("ner_merchant", "classifier")
        workflow.add_edge("classifier", "pattern_analyzer")
        workflow.add_edge("pattern_analyzer", "suggestion")
        workflow.add_edge("suggestion", "safety_guard")
        workflow.add_edge("safety_guard", END)
        
        # Set entry point to NER merchant
        workflow.set_entry_point("ner_merchant")
        
        # Compile workflow
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        
        # Create initial state with preprocessed data
        initial_state = TransactionProcessingState(
            raw_transactions=[],
            preprocessed_transactions=[t.dict() if hasattr(t, 'dict') else t.__dict__ for t in preprocessed_transactions],
            merchant_transactions=[],
            classified_transactions=[],
            pattern_insights=[],
            suggestions=[],
            security_alerts=[],
            current_step="ingestion_complete",
            metadata={}
        )

        # Run the workflow with proper configuration
        config = {
            "configurable": {
                "thread_id": "preprocessed_thread_001"
            }
        }
        
        # Run the workflow
        final_state = await app.ainvoke(initial_state, config)
        
        return {
            "processed_transactions": final_state["classified_transactions"],
            "insights": final_state["pattern_insights"],
            "suggestions": final_state["suggestions"],
            "security_alerts": final_state["security_alerts"],
            "metadata": final_state["metadata"]
        }


class TransactionProcessingWorkflow:
    """
    LangGraph-based workflow for comprehensive transaction processing
    Integrates with the states and nodes for complete pipeline orchestration
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LangGraph workflow
        
        Args:
            config: Optional configuration dictionary
        """
        from config.settings import get_settings
        
        # Get configuration
        self.config = config or {}
        self.settings = get_settings()
        
        # Initialize processing nodes
        from ..nodes import TransactionProcessingNodes
        self.nodes = TransactionProcessingNodes(config=self.config)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        from langgraph.graph import StateGraph
        from langgraph.checkpoint.memory import MemorySaver
        from ..states import TransactionProcessingState
        
        # Create the workflow graph
        workflow = StateGraph(TransactionProcessingState)
        
        # Add nodes
        workflow.add_node("initialize", self.nodes.initialize_workflow_node)
        workflow.add_node("nl_processing", self.nodes.nl_processing_node)
        workflow.add_node("ingestion", self.nodes.ingestion_node)
        workflow.add_node("ner_extraction", self.nodes.ner_extraction_node)
        workflow.add_node("classification", self.nodes.classification_node)
        workflow.add_node("validation", self.nodes.validation_node)
        workflow.add_node("finalization", self.nodes.finalization_node)
        
        # Define the flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "nl_processing")
        workflow.add_edge("nl_processing", "ingestion")
        workflow.add_edge("ingestion", "ner_extraction")
        workflow.add_edge("ner_extraction", "classification")
        workflow.add_edge("classification", "validation")
        workflow.add_edge("validation", "finalization")
        workflow.set_finish_point("finalization")
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def process_transaction(self, user_input: str, user_id: str = "default", 
                                conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single transaction through the complete workflow
        
        Args:
            user_input: Natural language transaction description
            user_id: User identifier
            conversation_context: Additional context
            
        Returns:
            Dictionary with processing results
        """
        from ..states import TransactionProcessingState, ProcessingStage
        from datetime import datetime
        
        # Create initial state
        initial_state = TransactionProcessingState(
            user_input=user_input,
            user_id=user_id,
            conversation_context=conversation_context or {},
            current_stage=ProcessingStage.INITIAL,
            processed_transactions=[],
            confidence_scores=[],
            processing_history=[],
            error_log=[],
            created_at=datetime.now()
        )
        
        # Execute workflow
        config = {"configurable": {"thread_id": f"user_{user_id}"}}
        result = await self.workflow.ainvoke(initial_state, config=config)
        
        return result
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get the current workflow status and capabilities"""
        return {
            "status": "ready",
            "nodes": [
                "initialize", "nl_processing", "ingestion", 
                "ner_extraction", "classification", "validation", "finalization"
            ],
            "capabilities": [
                "Natural language transaction processing",
                "Automatic merchant extraction",
                "Category classification",
                "Confidence scoring",
                "Error handling"
            ],
            "config": bool(self.config)
        }
