"""
Workflow Service
Transforms prediction_results into workflow status for monitoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow status and monitoring"""

    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)

    def _map_stage_to_agent(self, stage: Optional[str]) -> str:
        """Map processing stage to agent name"""
        stage_mapping = {
            "initial": "Workflow Initializer",
            "nl_processing": "Natural Language Processor",
            "ingestion": "Enhanced Ingestion Agent",
            "ner_extraction": "NER Extraction Agent",
            "classification": "Classification Agent",
            "pattern_analysis": "Pattern Analysis Agent",
            "suggestion": "Suggestion Agent",
            "safety_guard": "Safety Guard Agent",
            "validation": "Validation Agent",
            "finalization": "Finalization Agent",
            "completed": "Completed",
            "error": "Error Handler"
        }
        return stage_mapping.get(stage or "", "Unknown Agent")

    def _calculate_progress(self, status: str, current_stage: Optional[str]) -> int:
        """Calculate progress percentage based on status and stage"""
        if status == "completed":
            return 100
        if status == "failed":
            return 0
        if status == "pending":
            return 0

        # For processing status, calculate based on stage
        stage_progress = {
            "initial": 5,
            "nl_processing": 15,
            "ingestion": 30,
            "ner_extraction": 45,
            "classification": 60,
            "pattern_analysis": 70,
            "suggestion": 85,
            "safety_guard": 90,
            "validation": 95,
            "finalization": 98,
            "completed": 100
        }
        return stage_progress.get(current_stage or "", 50)

    def _transform_to_workflow_status(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Transform prediction_result record to workflow status format"""
        status = prediction.get("status", "pending")
        current_stage = prediction.get("current_stage")

        # Use source_name directly if available
        source_name = prediction.get("source_name")
        if not source_name:
            # Only generate fallback if source_name is truly missing
            input_type = prediction.get("input_type", "upload")
            if input_type == "structured":
                source_name = f"CSV Upload ({prediction.get('raw_transaction_count', 0)} transactions)"
            elif input_type == "conversational":
                user_input = prediction.get("user_input", "")
                source_name = f"Chat: {user_input[:50]}..." if user_input else "Manual Entry"
            else:
                source_name = f"Workflow {prediction.get('workflow_id', 'unknown')[:16]}..."

        return {
            "workflow_id": prediction.get("workflow_id"),
            "status": status,
            "current_agent": self._map_stage_to_agent(current_stage),
            "progress": self._calculate_progress(status, current_stage),
            "start_time": prediction.get("created_at"),
            "end_time": prediction.get("completed_at"),
            "source_name": source_name,
            "result": {
                "transactions_processed": prediction.get("raw_transaction_count", 0),
                "category": prediction.get("predicted_category"),
                "merchant": prediction.get("merchant_name"),
                "confidence": prediction.get("category_confidence"),
                "insights_generated": len(prediction.get("pattern_insights", []) or []),
                "suggestions_count": (
                    len(prediction.get("budget_recommendations", []) or []) +
                    len(prediction.get("spending_suggestions", []) or []) +
                    len(prediction.get("savings_opportunities", []) or [])
                )
            }
        }

    def _transform_to_processing_log(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Transform prediction_result to processing log format"""
        # Use source_name directly if available
        source_name = prediction.get("source_name")
        if not source_name:
            # Only generate fallback if source_name is truly missing
            input_type = prediction.get("input_type", "upload")
            if input_type == "structured":
                source_name = f"CSV Upload ({prediction.get('raw_transaction_count', 0)} transactions)"
            elif input_type == "conversational":
                user_input = prediction.get("user_input", "")
                source_name = f"Chat: {user_input[:50]}..." if user_input else "Manual Entry"
            else:
                source_name = f"Workflow {prediction.get('workflow_id', 'unknown')[:16]}..."

        return {
            "timestamp": prediction.get("created_at"),
            "file": f"Workflow {prediction.get('workflow_id', 'unknown')[:8]}",
            "source_name": source_name,
            "transactions": prediction.get("raw_transaction_count", 0),
            "status": prediction.get("status", "unknown"),
            "workflow_id": prediction.get("workflow_id")
        }

    def get_workflow_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get workflow statistics for a user"""
        try:
            # Get all workflows for user
            result = self.supabase.table("prediction_results").select(
                "workflow_id, status, created_at"
            ).eq("user_id", user_id).execute()

            workflows = result.data or []

            # Count by status
            completed = sum(1 for w in workflows if w.get("status") == "completed")
            processing = sum(1 for w in workflows if w.get("status") == "processing")
            pending = sum(1 for w in workflows if w.get("status") == "pending")
            failed = sum(1 for w in workflows if w.get("status") == "failed")

            return {
                "total": len(workflows),
                "completed": completed,
                "processing": processing,
                "pending": pending,
                "failed": failed
            }

        except Exception as e:
            logger.error(f"Error fetching workflow statistics: {e}", exc_info=True)
            return {
                "total": 0,
                "completed": 0,
                "processing": 0,
                "pending": 0,
                "failed": 0
            }

    def get_active_workflows(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active (processing or pending) workflows for a user"""
        try:
            result = self.supabase.table("prediction_results").select(
                "workflow_id, status, current_stage, started_at, completed_at, "
                "raw_transaction_count, predicted_category, merchant_name, "
                "category_confidence, pattern_insights, budget_recommendations, "
                "spending_suggestions, savings_opportunities, created_at, source_name, "
                "input_type, user_input"
            ).eq("user_id", user_id).in_("status", ["pending", "processing", "completed"]).order(
                "started_at", desc=True
            ).limit(limit).execute()

            workflows = result.data or []
            return [self._transform_to_workflow_status(w) for w in workflows]

        except Exception as e:
            logger.error(f"Error fetching active workflows: {e}", exc_info=True)
            return []

    def get_workflow_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get processing history/logs for a user"""
        try:
            result = self.supabase.table("prediction_results").select(
                "workflow_id, status, raw_transaction_count, created_at, source_name, "
                "input_type, user_input"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

            workflows = result.data or []
            return [self._transform_to_processing_log(w) for w in workflows]

        except Exception as e:
            logger.error(f"Error fetching workflow history: {e}", exc_info=True)
            return []

    def get_workflow_by_id(self, workflow_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific workflow details"""
        try:
            result = self.supabase.table("prediction_results").select(
                "*"
            ).eq("workflow_id", workflow_id).eq("user_id", user_id).single().execute()

            if result.data:
                return self._transform_to_workflow_status(result.data)
            return None

        except Exception as e:
            logger.error(f"Error fetching workflow {workflow_id}: {e}", exc_info=True)
            return None

    def get_agent_communications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent communication logs from processing history with detailed information"""
        try:
            result = self.supabase.table("prediction_results").select(
                "workflow_id, processing_history, created_at, status, source_name, "
                "input_type, raw_transaction_count, predicted_category, merchant_name"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

            # Use a dict to deduplicate by workflow_id + stage
            workflow_communications = {}

            # Define stages to show - only meaningful agent stages
            important_stages = {
                "ingestion",
                "ner_extraction",
                "classification",
                "pattern_analysis",
                "suggestion",
                "safety_guard",
                "validation"
            }

            for workflow in (result.data or []):
                processing_history = workflow.get("processing_history", [])
                workflow_id = workflow.get("workflow_id", "unknown")
                workflow_short_id = workflow_id[:8]

                # Get source name for context
                source_name = workflow.get("source_name")
                if not source_name:
                    input_type = workflow.get("input_type", "upload")
                    tx_count = workflow.get("raw_transaction_count", 0)
                    if input_type == "structured":
                        source_name = f"CSV Upload ({tx_count} txns)"
                    elif input_type == "conversational":
                        source_name = "Chat"
                    else:
                        source_name = "Upload"

                if processing_history and isinstance(processing_history, list):
                    for entry in processing_history:
                        if isinstance(entry, dict):
                            # Extract communication details
                            stage = entry.get("stage", "unknown")

                            # Skip stages that aren't in our important list
                            if stage not in important_stages:
                                continue

                            timestamp = entry.get("timestamp") or workflow.get("created_at")
                            base_message = entry.get("message", "")
                            status = entry.get("status", "info")
                            details = entry.get("details", {})

                            # Create unique key for deduplication: workflow_id + stage
                            dedup_key = f"{workflow_id}_{stage}"

                            # Only keep the most recent entry for each workflow + stage combination
                            if dedup_key not in workflow_communications:
                                # Create agent communication entry
                                agent_name = self._map_stage_to_agent(stage)

                                # Enhance message with context from details
                                enhanced_message = self._enhance_message(
                                    base_message,
                                    stage,
                                    details,
                                    workflow,
                                    source_name
                                )

                                workflow_communications[dedup_key] = {
                                    "timestamp": timestamp,
                                    "workflow_id": workflow_short_id,
                                    "agent": agent_name,
                                    "stage": stage,
                                    "message": enhanced_message,
                                    "status": status,
                                    "details": details
                                }

            # Convert dict to list and sort by timestamp descending (most recent first)
            communications = list(workflow_communications.values())
            communications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return communications[:limit]

        except Exception as e:
            logger.error(f"Error fetching agent communications: {e}", exc_info=True)
            return []

    def _enhance_message(
        self,
        base_message: str,
        stage: str,
        details: Dict[str, Any],
        workflow: Dict[str, Any],
        source_name: str
    ) -> str:
        """Enhance message with contextual information"""
        if not base_message or base_message.endswith("completed"):
            # Generate more descriptive messages based on stage and details
            if stage == "ingestion":
                tx_count = details.get("transaction_count") or workflow.get("raw_transaction_count", 0)
                return f"Processed {tx_count} transactions from {source_name}"

            elif stage == "classification":
                category = workflow.get("predicted_category")
                confidence = details.get("confidence") or workflow.get("category_confidence")
                if category and confidence:
                    return f"Classified as '{category}' with {confidence*100:.1f}% confidence"
                return f"Completed transaction classification for {source_name}"

            elif stage == "ner_extraction":
                merchant = details.get("merchant") or workflow.get("merchant_name")
                if merchant:
                    return f"Identified merchant: {merchant}"
                return "Extracted merchant and entity information"

            elif stage == "pattern_analysis":
                patterns_found = details.get("patterns_detected", 0)
                if patterns_found:
                    return f"Detected {patterns_found} spending patterns"
                return "Analyzed transaction patterns and trends"

            elif stage == "suggestion":
                suggestions = details.get("suggestions_count", 0)
                if suggestions:
                    return f"Generated {suggestions} personalized recommendations"
                return "Created budget and savings suggestions"

            elif stage == "safety_guard":
                fraud_score = details.get("fraud_score")
                if fraud_score and fraud_score > 0.5:
                    return f"⚠️ Security alert: Fraud score {fraud_score*100:.1f}%"
                return "Security validation passed - no anomalies detected"

            elif stage == "validation":
                valid = details.get("is_valid", True)
                if valid:
                    return "Data quality validation successful"
                return "⚠️ Validation issues detected"

            else:
                return base_message or f"Completed {stage} stage"

        return base_message


# Singleton instance
_workflow_service: Optional[WorkflowService] = None


def get_workflow_service() -> WorkflowService:
    """Get or create the singleton workflow service"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service
