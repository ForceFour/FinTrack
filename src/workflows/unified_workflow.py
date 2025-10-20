"""
Unified LangGraph Workflow Manager
Complete implementation of the 7-agent transaction processing pipeline
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client

from ..states import TransactionProcessingState, ProcessingStage
from ..nodes import TransactionProcessingNodes
from .config import WorkflowMode, LangGraphConfig, get_workflow_config, setup_langchain_environment

logger = logging.getLogger(__name__)

class UnifiedTransactionWorkflow:
    """
    Unified LangGraph Workflow Manager for Complete Transaction Processing

    Features:
    - 6 specialized AI agents with intelligent routing
    - Multiple execution modes with optimization
    - Real-time processing with WebSocket support
    - Comprehensive error handling and recovery
    - LangSmith tracing and monitoring
    - Background processing capabilities
    - Checkpoint-based persistence
    """

    def __init__(self, config: Optional[LangGraphConfig] = None):
        """Initialize the unified workflow system"""

        # Load configuration
        self.config = config or get_workflow_config()

        # Setup LangChain environment
        setup_langchain_environment(self.config)

        # Initialize LangSmith client if tracing enabled
        self.langsmith_client = None
        if self.config.enable_tracing:
            try:
                self.langsmith_client = Client(
                    api_key=self.config.langsmith_api_key,
                    api_url=self.config.langsmith_endpoint
                )
                logger.info("LangSmith client initialized for workflow tracing")
            except Exception as e:
                logger.warning(f"LangSmith client initialization failed: {e}")
                self.config.enable_tracing = False

        # Initialize processing nodes with agent configuration
        agent_config = {
            'groq_api_key': self.config.groq_api_key,
            'langgraph_api_key': self.config.langgraph_api_key,
            'langsmith_api_key': self.config.langsmith_api_key,
            'openai_api_key': self.config.openai_api_key,
            'confidence_threshold': self.config.confidence_threshold,
            'enable_parallel_processing': self.config.enable_parallel_processing
        }

        self.nodes = TransactionProcessingNodes(config=agent_config)

        # Initialize checkpointer based on configuration
        self.checkpointer = self._initialize_checkpointer()

        # Build all workflow modes
        self.workflows = self._build_all_workflows()

        # Workflow execution tracking
        self.active_workflows = {}
        self.workflow_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_processing_time': 0.0,
            'agent_performance': {},
            'mode_usage': {mode.value: 0 for mode in WorkflowMode}
        }

        # Background task queue
        self.background_tasks = {}

        logger.info("UnifiedTransactionWorkflow initialized successfully")
        logger.info(f"Configuration: {len(self.workflows)} modes, tracing={'enabled' if self.config.enable_tracing else 'disabled'}")

    def _initialize_checkpointer(self):
        """Initialize the appropriate checkpointer based on configuration"""
        # Temporarily disable checkpointer to avoid version compatibility issues
        logger.info("Using memory-only checkpointer for better compatibility")
        return MemorySaver()

    def _build_all_workflows(self) -> Dict[str, StateGraph]:
        """Build all workflow graphs for different execution modes"""
        workflows = {}

        try:
            # Full pipeline workflow (all 7 agents)
            workflows[WorkflowMode.FULL_PIPELINE.value] = self._build_full_pipeline()

            # Quick classification workflow
            workflows[WorkflowMode.QUICK_CLASSIFICATION.value] = self._build_quick_classification()

            # Ingestion-only workflow
            workflows[WorkflowMode.INGESTION_ONLY.value] = self._build_ingestion_only()

            # Validation-only workflow
            workflows[WorkflowMode.VALIDATION_ONLY.value] = self._build_validation_only()

            # Background processing workflow
            workflows[WorkflowMode.BACKGROUND_PROCESSING.value] = self._build_background_processing()

            logger.info(f"Built {len(workflows)} workflow modes successfully")

        except Exception as e:
            logger.error(f"❌ Failed to build workflows: {e}")
            raise

        return workflows

    def _build_full_pipeline(self) -> StateGraph:
        """Build the complete 10-agent pipeline workflow with conditional routing"""
        workflow = StateGraph(TransactionProcessingState)

        # Add all workflow nodes
        workflow.add_node("🔧 Initialize", self.nodes.initialize_workflow_node)
        workflow.add_node("🧠 NL Processing", self.nodes.nl_processing_node)
        workflow.add_node("🚀 Ingestion", self.nodes.ingestion_node)
        workflow.add_node("🏷️ NER Extraction", self.nodes.ner_extraction_node)
        workflow.add_node("📊 Classification", self.nodes.classification_node)
        workflow.add_node("📈 Pattern Analysis", self.nodes.pattern_analyzer_node)
        workflow.add_node("💡 Suggestion", self.nodes.suggestion_node)
        workflow.add_node("🛡️ Safety Guard", self.nodes.safety_guard_node)
        workflow.add_node("✅ Validation", self.nodes.validation_node)
        workflow.add_node("🎯 Finalization", self.nodes.finalization_node)

        # Add conditional routing node
        workflow.add_node("🔀 Router", self._routing_node)

        # Define the complete pipeline flow
        workflow.set_entry_point("🔧 Initialize")

        # Main pipeline
        workflow.add_edge("🔧 Initialize", "🧠 NL Processing")
        workflow.add_edge("🧠 NL Processing", "🚀 Ingestion")
        workflow.add_edge("🚀 Ingestion", "🔀 Router")

        # Conditional routing from Router
        workflow.add_conditional_edges(
            "🔀 Router",
            self._should_continue_processing,
            {
                "continue": "🏷️ NER Extraction",
                "skip_to_validation": "✅ Validation",
                "error": "🎯 Finalization"
            }
        )

        # Continue with full processing
        workflow.add_edge("🏷️ NER Extraction", "📊 Classification")
        workflow.add_edge("📊 Classification", "📈 Pattern Analysis")
        workflow.add_edge("📈 Pattern Analysis", "💡 Suggestion")
        workflow.add_edge("💡 Suggestion", "🛡️ Safety Guard")
        workflow.add_edge("🛡️ Safety Guard", "✅ Validation")
        workflow.add_edge("✅ Validation", "🎯 Finalization")
        workflow.add_edge("🎯 Finalization", END)

        return workflow

    def _build_quick_classification(self) -> StateGraph:
        """Build quick classification workflow (essential processing only)"""
        workflow = StateGraph(TransactionProcessingState)

        # Essential nodes for quick processing
        workflow.add_node("🔧 Initialize", self.nodes.initialize_workflow_node)
        workflow.add_node("🧠 NL Processing", self.nodes.nl_processing_node)
        workflow.add_node("🚀 Ingestion", self.nodes.ingestion_node)
        workflow.add_node("📊 Classification", self.nodes.classification_node)
        workflow.add_node("🎯 Finalization", self.nodes.finalization_node)

        # Quick flow
        workflow.set_entry_point("🔧 Initialize")
        workflow.add_edge("🔧 Initialize", "🧠 NL Processing")
        workflow.add_edge("🧠 NL Processing", "🚀 Ingestion")
        workflow.add_edge("🚀 Ingestion", "📊 Classification")
        workflow.add_edge("📊 Classification", "🎯 Finalization")
        workflow.add_edge("🎯 Finalization", END)

        return workflow

    def _build_ingestion_only(self) -> StateGraph:
        """Build ingestion-only workflow for data preprocessing"""
        workflow = StateGraph(TransactionProcessingState)

        workflow.add_node("🔧 Initialize", self.nodes.initialize_workflow_node)
        workflow.add_node("🧠 NL Processing", self.nodes.nl_processing_node)
        workflow.add_node("🚀 Ingestion", self.nodes.ingestion_node)
        workflow.add_node("🎯 Finalization", self.nodes.finalization_node)

        workflow.set_entry_point("🔧 Initialize")
        workflow.add_edge("🔧 Initialize", "🧠 NL Processing")
        workflow.add_edge("🧠 NL Processing", "🚀 Ingestion")
        workflow.add_edge("🚀 Ingestion", "🎯 Finalization")
        workflow.add_edge("🎯 Finalization", END)

        return workflow

    def _build_validation_only(self) -> StateGraph:
        """Build validation-only workflow for quick checks"""
        workflow = StateGraph(TransactionProcessingState)

        workflow.add_node("🔧 Initialize", self.nodes.initialize_workflow_node)
        workflow.add_node("🧠 NL Processing", self.nodes.nl_processing_node)
        workflow.add_node("✅ Validation", self.nodes.validation_node)
        workflow.add_node("🎯 Finalization", self.nodes.finalization_node)

        workflow.set_entry_point("🔧 Initialize")
        workflow.add_edge("🔧 Initialize", "🧠 NL Processing")
        workflow.add_edge("🧠 NL Processing", "✅ Validation")
        workflow.add_edge("✅ Validation", "🎯 Finalization")
        workflow.add_edge("🎯 Finalization", END)

        return workflow

    def _build_background_processing(self) -> StateGraph:
        """Build background processing workflow with async capabilities"""
        workflow = StateGraph(TransactionProcessingState)

        # Background nodes with async processing
        workflow.add_node("🔧 Background Init", self._background_init_node)
        workflow.add_node("🚀 Background Ingestion", self._background_ingestion_node)
        workflow.add_node("🔍 Background Processing", self._background_processing_node)
        workflow.add_node("🎯 Background Finalization", self._background_finalization_node)

        workflow.set_entry_point("🔧 Background Init")
        workflow.add_edge("🔧 Background Init", "🚀 Background Ingestion")
        workflow.add_edge("🚀 Background Ingestion", "🔍 Background Processing")
        workflow.add_edge("🔍 Background Processing", "🎯 Background Finalization")
        workflow.add_edge("🎯 Background Finalization", END)

        return workflow

    # ==========================================
    # WORKFLOW NODE IMPLEMENTATIONS
    # ==========================================

    def _routing_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Intelligent routing node to determine processing path"""
        logger.info("ROUTER: Determining optimal processing path")

        try:
            # Check ingestion results
            preprocessed_txns = state.get("preprocessed_transactions", [])
            ingestion_confidence = state.get("ingestion_confidence", 0.0)
            errors = state.get("error_log", [])

            # Updated routing logic - Always continue to advanced processing unless critical errors
            if errors and any(error.get("severity") == "critical" for error in errors):
                logger.warning(f"Critical errors detected: {len(errors)}, routing to error handling")
                state["route_decision"] = "error"
                state["skip_reason"] = "critical_errors_detected"
            elif not preprocessed_txns and not state.get("user_input"):
                logger.warning("No transactions and no user input, skipping to validation")
                state["route_decision"] = "skip_to_validation"
                state["skip_reason"] = "no_data_to_process"
            else:
                # Always continue to advanced processing - Pattern Analysis, Suggestions, Safety Guard should run
                # even for first-time users or low confidence scenarios
                logger.info(f"Continuing to advanced processing with {len(preprocessed_txns)} transactions and {ingestion_confidence:.2f} confidence")
                state["route_decision"] = "continue"

                # Add note about first-time user scenario
                if not preprocessed_txns or len(preprocessed_txns) == 1:
                    state["first_time_user_scenario"] = True
                    logger.info("ROUTER: First-time user scenario detected - will provide default suggestions")

            # Add routing history
            state["processing_history"].append({
                "stage": "routing_decision",
                "timestamp": datetime.now().isoformat(),
                "decision": state["route_decision"],
                "reason": state.get("skip_reason", "normal_processing"),
                "transactions_count": len(preprocessed_txns),
                "confidence": ingestion_confidence,
                "first_time_user": state.get("first_time_user_scenario", False)
            })

        except Exception as e:
            logger.error(f"❌ ROUTER failed: {e}")
            state["route_decision"] = "error"
            state["error_log"].append({
                "stage": "routing_decision",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        return state

    def _should_continue_processing(self, state: TransactionProcessingState) -> str:
        """Determine the routing decision from the router node"""
        return state.get("route_decision", "continue")

    # Background processing nodes
    def _background_init_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Initialize background processing"""
        state["background_processing"] = True
        state["async_task_id"] = f"bg_task_{uuid.uuid4().hex[:8]}"
        state["processing_mode"] = "background"

        logger.info(f"BACKGROUND INIT: Started async task {state['async_task_id']}")

        return self.nodes.initialize_workflow_node(state)

    def _background_ingestion_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Background ingestion processing"""
        logger.info("BACKGROUND INGESTION: Processing in background mode")

        # Run NL processing and ingestion
        state = self.nodes.nl_processing_node(state)
        state = self.nodes.ingestion_node(state)

        # Mark as background processed
        if "ingestion_metadata" in state:
            state["ingestion_metadata"]["background_processing"] = True
            state["ingestion_metadata"]["task_id"] = state.get("async_task_id")

        return state

    def _background_processing_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Background processing combining multiple agents"""
        logger.info("BACKGROUND PROCESSING: Running combined agent processing")

        # Run NER extraction and classification
        state = self.nodes.ner_extraction_node(state)
        state = self.nodes.classification_node(state)
        state = self.nodes.validation_node(state)

        return state

    def _background_finalization_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """Background finalization with notification capabilities"""
        logger.info("🎯 BACKGROUND FINALIZATION: Completing async processing")

        # Run standard finalization
        result_state = self.nodes.finalization_node(state)

        # Add background-specific metadata
        if "workflow_summary" in result_state:
            result_state["workflow_summary"]["processing_mode"] = "background"
            result_state["workflow_summary"]["async_task_id"] = state.get("async_task_id")
            result_state["workflow_summary"]["notification_ready"] = True

        return result_state

    def _calculate_overall_confidence(self, final_state: Dict[str, Any]) -> float:
        """
        Calculate overall workflow confidence based on individual stage confidences

        Args:
            final_state: The final workflow state containing confidence data

        Returns:
            Overall confidence score between 0.0 and 1.0
        """
        confidence_scores = []

        # Extract confidence from various stages
        ingestion_confidence = final_state.get("ingestion_confidence", 0.0)
        if ingestion_confidence > 0:
            confidence_scores.append(ingestion_confidence)

        # NL processing confidence
        nl_confidence = final_state.get("nl_confidence", 0.0)
        if nl_confidence > 0:
            confidence_scores.append(nl_confidence)

        # Classification confidence
        category_confidence = final_state.get("category_confidence", 0.0)
        if category_confidence > 0:
            confidence_scores.append(category_confidence)

        # Pattern analysis confidence (based on insights found)
        pattern_insights = final_state.get("pattern_insights", [])
        if pattern_insights:
            pattern_confidence = min(0.85, 0.6 + (len(pattern_insights) * 0.05))  # Cap at 0.85
            confidence_scores.append(pattern_confidence)

        # Suggestion confidence (based on suggestions generated)
        budget_recommendations = final_state.get("budget_recommendations", [])
        spending_suggestions = final_state.get("spending_suggestions", [])
        if budget_recommendations or spending_suggestions:
            suggestion_confidence = 0.75  # Good confidence if suggestions were generated
            confidence_scores.append(suggestion_confidence)

        # Safety guard confidence (based on risk assessment)
        security_alerts = final_state.get("security_alerts", [])
        risk_assessment = final_state.get("risk_assessment", {})
        if security_alerts or risk_assessment:
            safety_confidence = 0.8  # High confidence if safety analysis was performed
            confidence_scores.append(safety_confidence)

        # If no confidence scores available, check for successful processing
        if not confidence_scores:
            processed_transactions = final_state.get("processed_transactions", [])
            if processed_transactions:
                confidence_scores.append(0.5)  # Minimum confidence for successful processing

        # Calculate weighted average confidence
        if confidence_scores:
            # Weight more recent/complex stages higher
            weights = [1.0] * len(confidence_scores)  # Equal weights for now
            if len(confidence_scores) > 1:
                # Give slightly higher weight to advanced agents (pattern, suggestion, safety)
                for i in range(max(0, len(confidence_scores) - 3), len(confidence_scores)):
                    weights[i] = 1.2

            weighted_sum = sum(score * weight for score, weight in zip(confidence_scores, weights))
            total_weights = sum(weights)
            overall_confidence = weighted_sum / total_weights
        else:
            overall_confidence = 0.0

        return min(1.0, max(0.0, overall_confidence))  # Ensure between 0-1

    # ==========================================
    # WORKFLOW EXECUTION METHODS
    # ==========================================

    async def _load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Load user profile with spending limits from database
        """
        try:
            from ..core.database_config import get_db_client

            supabase = await get_db_client()

            # Get user profile from profiles table
            result = supabase.table("profiles").select("*").eq("id", user_id).execute()

            if result.data and len(result.data) > 0:
                profile = result.data[0]
                return {
                    'user_id': user_id,
                    'spending_limits': profile.get('spending_limits', {}),
                    'historical_amounts': profile.get('historical_amounts', []),
                    'frequency_threshold': profile.get('frequency_threshold', 10),
                    'category_frequency_threshold': profile.get('category_frequency_threshold', 15),
                    'location_repetition_threshold': profile.get('location_repetition_threshold', 15),
                    'is_new_user': False,
                    'has_seen_security_recommendations': True
                }
            else:
                # New user - return default profile
                return {
                    'user_id': user_id,
                    'spending_limits': {},
                    'historical_amounts': [],
                    'frequency_threshold': 10,
                    'category_frequency_threshold': 15,
                    'location_repetition_threshold': 15,
                    'is_new_user': True,
                    'has_seen_security_recommendations': False
                }

        except Exception as e:
            logger.warning(f"Failed to load user profile: {e}, using defaults")
            return {
                'user_id': user_id,
                'spending_limits': {},
                'historical_amounts': [],
                'frequency_threshold': 10,
                'category_frequency_threshold': 15,
                'location_repetition_threshold': 15,
                'is_new_user': True,
                'has_seen_security_recommendations': False
            }

    async def execute_workflow(self,
                             mode: WorkflowMode = WorkflowMode.FULL_PIPELINE,
                             user_input: str = None,
                             raw_transactions: List[Dict[str, Any]] = None,
                             user_id: str = "default",
                             conversation_context: Dict[str, Any] = None,
                             custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the complete transaction workflow

        Args:
            mode: Workflow execution mode
            user_input: Natural language input for processing
            raw_transactions: Raw transaction data for structured processing
            user_id: User identifier
            conversation_context: Conversation state for multi-turn interactions
            custom_config: Runtime configuration overrides

        Returns:
            Complete workflow results with all agent outputs
        """

        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()

        logger.info(f"Starting workflow {workflow_id} in {mode.value} mode")

        try:
            # Update mode usage statistics
            self.workflow_stats["mode_usage"][mode.value] += 1

            # Select appropriate workflow
            if mode.value not in self.workflows:
                raise ValueError(f"Workflow mode {mode.value} not available. Available: {list(self.workflows.keys())}")

            workflow_graph = self.workflows[mode.value]

            # Determine input type
            input_type = "structured" if raw_transactions else "unstructured"

            # Load user profile with spending limits
            user_profile = await self._load_user_profile(user_id)

            # Initialize state
            initial_state = TransactionProcessingState(
                workflow_id=workflow_id,
                user_input=user_input or "",
                user_id=user_id,
                conversation_context=conversation_context or {},
                raw_transactions=raw_transactions or [],
                input_type=input_type,  # Add input_type to state
                current_stage=ProcessingStage.INITIAL,
                processing_history=[],
                confidence_scores=[],
                error_log=[],
                processed_transactions=[],
                started_at=start_time,
                created_at=start_time,
                user_profile=user_profile  # Add user profile with spending limits
            )

            # Add workflow start to history
            initial_state["processing_history"].append({
                "stage": "workflow_start",
                "timestamp": start_time.isoformat(),
                "mode": mode.value,
                "workflow_id": workflow_id,
                "input_type": input_type,
                "user_id": user_id
            })

            # Compile workflow without checkpointer for better compatibility
            app = workflow_graph.compile()

            # Configure workflow execution
            workflow_config = {"configurable": {"thread_id": workflow_id}}

            # Add custom configuration if provided
            if custom_config:
                workflow_config["configurable"].update(custom_config)

            # Add tracing if enabled
            if self.config.enable_tracing and self.langsmith_client:
                workflow_config["callbacks"] = [LangChainTracer(project_name=self.config.langsmith_project)]
                logger.info(f"LangSmith tracing enabled for workflow {workflow_id}")

            # Execute workflow with timeout
            logger.info(f"Executing {mode.value} workflow with timeout {self.config.timeout_seconds}s...")

            try:
                final_state = await asyncio.wait_for(
                    app.ainvoke(initial_state, config=workflow_config),
                    timeout=self.config.timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ Workflow {workflow_id} timed out after {self.config.timeout_seconds}s")
                raise TimeoutError(f"Workflow execution timed out after {self.config.timeout_seconds} seconds")

            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Track successful workflow
            self.active_workflows[workflow_id] = {
                "status": "completed",
                "mode": mode.value,
                "start_time": start_time,
                "end_time": end_time,
                "execution_time": execution_time,
                "result": final_state,
                "user_id": user_id
            }

            # Update statistics
            self._update_workflow_stats(workflow_id, execution_time, True)

            # Calculate overall confidence from all stages
            overall_confidence = self._calculate_overall_confidence(final_state)

            logger.info(f"Workflow {workflow_id} completed successfully in {execution_time:.2f}s with {overall_confidence:.2f} confidence")

            return {
                "workflow_id": workflow_id,
                "status": "success",
                "mode": mode.value,
                "execution_time": execution_time,
                "result": final_state,
                "stages_completed": len(final_state.get("processing_history", [])),
                "transactions_processed": len(final_state.get("processed_transactions", [])),
                "confidence_scores": final_state.get("confidence_scores", []),
                "overall_confidence": overall_confidence,
                "user_id": user_id
            }

        except Exception as e:
            # Calculate execution time for failed workflow
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            logger.error(f"❌ Workflow {workflow_id} failed after {execution_time:.2f}s: {e}")

            # Track failed workflow
            self.active_workflows[workflow_id] = {
                "status": "failed",
                "mode": mode.value,
                "start_time": start_time,
                "end_time": end_time,
                "execution_time": execution_time,
                "error": str(e),
                "user_id": user_id
            }

            # Update statistics
            self._update_workflow_stats(workflow_id, execution_time, False)

            return {
                "workflow_id": workflow_id,
                "status": "error",
                "mode": mode.value,
                "execution_time": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": user_id
            }

    def execute_workflow_sync(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for workflow execution"""
        return asyncio.run(self.execute_workflow(**kwargs))

    async def execute_background_workflow(self,
                                        user_input: str = None,
                                        raw_transactions: List[Dict[str, Any]] = None,
                                        user_id: str = "default",
                                        notification_callback: Optional[Callable] = None) -> str:
        """
        Execute workflow in background mode with optional notifications

        Returns:
            Task ID for tracking background execution
        """

        task_id = f"bg_task_{uuid.uuid4().hex[:8]}"
        logger.info(f"🔄 Starting background workflow {task_id}")

        async def background_task():
            try:
                result = await self.execute_workflow(
                    mode=WorkflowMode.BACKGROUND_PROCESSING,
                    user_input=user_input,
                    raw_transactions=raw_transactions,
                    user_id=user_id
                )

                # Store background task result
                self.background_tasks[task_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                }

                if notification_callback:
                    await notification_callback(task_id, result)

                logger.info(f"✅ Background workflow {task_id} completed successfully")
                return result

            except Exception as e:
                logger.error(f"❌ Background workflow {task_id} failed: {e}")

                self.background_tasks[task_id] = {
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }

                if notification_callback:
                    await notification_callback(task_id, {"status": "error", "error": str(e)})

        # Start background task
        asyncio.create_task(background_task())

        # Track background task
        self.background_tasks[task_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "user_id": user_id
        }

        return task_id

    # ==========================================
    # WORKFLOW MANAGEMENT AND MONITORING
    # ==========================================

    def _update_workflow_stats(self, workflow_id: str, execution_time: float, success: bool):
        """Update workflow execution statistics"""
        self.workflow_stats["total_executions"] += 1

        if success:
            self.workflow_stats["successful_executions"] += 1
        else:
            self.workflow_stats["failed_executions"] += 1

        # Update average execution time
        total_time = self.workflow_stats["average_processing_time"] * (self.workflow_stats["total_executions"] - 1)
        self.workflow_stats["average_processing_time"] = (total_time + execution_time) / self.workflow_stats["total_executions"]

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        elif workflow_id in self.background_tasks:
            return {
                "type": "background_task",
                **self.background_tasks[workflow_id]
            }
        else:
            return {"status": "not_found", "workflow_id": workflow_id}

    def get_background_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a background task"""
        return self.background_tasks.get(task_id, {"status": "not_found", "task_id": task_id})

    def get_all_workflows_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all workflows and system"""
        return {
            "workflow_stats": self.workflow_stats,
            "active_workflows_count": len(self.active_workflows),
            "background_tasks_count": len(self.background_tasks),
            "available_modes": [mode.value for mode in WorkflowMode],
            "configuration": {
                "tracing_enabled": self.config.enable_tracing,
                "background_processing_enabled": self.config.enable_background_processing,
                "persistence_enabled": self.config.enable_persistence,
                "parallel_processing_enabled": self.config.enable_parallel_processing,
                "confidence_threshold": self.config.confidence_threshold,
                "max_batch_size": self.config.max_transactions_per_batch
            },
            "system_health": {
                "nodes_initialized": True,
                "checkpointer_type": type(self.checkpointer).__name__,
                "langsmith_connected": self.langsmith_client is not None,
                "workflow_modes_available": len(self.workflows)
            }
        }

    def cleanup_completed_workflows(self, older_than_hours: int = 24) -> int:
        """Clean up completed workflows older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        # Clean up active workflows
        workflows_to_remove = []
        for workflow_id, workflow_info in self.active_workflows.items():
            end_time = workflow_info.get("end_time")
            if end_time and end_time < cutoff_time:
                workflows_to_remove.append(workflow_id)

        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]

        # Clean up background tasks
        tasks_to_remove = []
        for task_id, task_info in self.background_tasks.items():
            completed_at = task_info.get("completed_at")
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    if completed_time < cutoff_time:
                        tasks_to_remove.append(task_id)
                except ValueError:
                    pass

        for task_id in tasks_to_remove:
            del self.background_tasks[task_id]

        total_cleaned = len(workflows_to_remove) + len(tasks_to_remove)
        logger.info(f"🧹 Cleaned up {total_cleaned} old workflows and tasks")

        return total_cleaned

    def get_agent_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics for each agent/node"""
        agent_stats = {}

        for workflow_id, workflow_info in self.active_workflows.items():
            if "result" in workflow_info and "processing_history" in workflow_info["result"]:
                for entry in workflow_info["result"]["processing_history"]:
                    stage = entry.get("stage", "unknown")

                    if stage not in agent_stats:
                        agent_stats[stage] = {
                            "total_executions": 0,
                            "successful_executions": 0,
                            "failed_executions": 0,
                            "average_confidence": 0.0,
                            "total_processing_time": 0.0
                        }

                    agent_stats[stage]["total_executions"] += 1

                    if entry.get("status") == "completed":
                        agent_stats[stage]["successful_executions"] += 1
                    else:
                        agent_stats[stage]["failed_executions"] += 1

                    # Add confidence if available
                    confidence = entry.get("confidence", 0)
                    if confidence:
                        current_avg = agent_stats[stage]["average_confidence"]
                        total_count = agent_stats[stage]["total_executions"]
                        agent_stats[stage]["average_confidence"] = (current_avg * (total_count - 1) + confidence) / total_count

        return agent_stats

    def export_workflow_metrics(self) -> Dict[str, Any]:
        """Export comprehensive workflow metrics for monitoring"""
        return {
            "timestamp": datetime.now().isoformat(),
            "workflow_stats": self.workflow_stats,
            "agent_performance": self.get_agent_performance_stats(),
            "system_status": self.get_all_workflows_status(),
            "configuration": {
                "mode": self.config.default_mode.value,
                "tracing_enabled": self.config.enable_tracing,
                "confidence_threshold": self.config.confidence_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "max_batch_size": self.config.max_transactions_per_batch
            }
        }

# Global workflow instance (singleton pattern)
_workflow_instance: Optional[UnifiedTransactionWorkflow] = None

def get_workflow_instance(config: Optional[LangGraphConfig] = None) -> UnifiedTransactionWorkflow:
    """Get or create the global workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = UnifiedTransactionWorkflow(config=config)
        logger.info("🚀 Global UnifiedTransactionWorkflow instance created")
    return _workflow_instance

def reset_workflow_instance():
    """Reset the global workflow instance (useful for testing)"""
    global _workflow_instance
    _workflow_instance = None

# Export compiled workflows for LangGraph API
def _get_compiled_workflows():
    """Get compiled workflows from the global instance"""
    instance = get_workflow_instance()
    compiled_workflows = {}

    for mode_name, workflow_graph in instance.workflows.items():
        try:
            # Compile workflow without checkpointer for API compatibility
            compiled_workflows[mode_name] = workflow_graph.compile()
            logger.info(f"✅ Compiled workflow: {mode_name}")
        except Exception as e:
            logger.error(f"❌ Failed to compile workflow {mode_name}: {e}")

    return compiled_workflows

# Initialize and export compiled workflows
try:
    _compiled_workflows = _get_compiled_workflows()

    # Export individual workflows for LangGraph API
    full_pipeline = _compiled_workflows.get('full_pipeline')
    quick_classification = _compiled_workflows.get('quick_classification')
    ingestion_only = _compiled_workflows.get('ingestion_only')
    background_processing = _compiled_workflows.get('background_processing')

    logger.info(f"🚀 Exported {len(_compiled_workflows)} compiled workflows for LangGraph API")

except Exception as e:
    logger.error(f"❌ Failed to initialize compiled workflows: {e}")
    # Create fallback minimal workflows
    full_pipeline = None
    quick_classification = None
    ingestion_only = None
    background_processing = None
