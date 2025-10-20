"""
Prediction Results Service
Saves workflow results to Supabase prediction_results table
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PredictionResultsService:
    """Service for saving prediction results to Supabase"""

    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        # Try both possible environment variable names
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set in environment")

        self.supabase: Client = create_client(supabase_url, supabase_key)

    def save_prediction_result(
        self,
        workflow_id: str,
        user_id: str,
        workflow_state: Dict[str, Any],
        mode: str = "full_pipeline",
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        Save workflow execution results to prediction_results table

        Args:
            workflow_id: Unique workflow identifier
            user_id: User identifier
            workflow_state: Complete state from TransactionProcessingState
            mode: Workflow mode (full_pipeline, quick_classification, etc.)
            status: Final status (completed, failed, partial)

        Returns:
            Saved prediction result record
        """
        try:
            # Check if workflow result already exists to prevent duplicates
            existing_result = self.get_prediction_result(workflow_id)
            if existing_result:
                logger.info(f"Prediction result for workflow {workflow_id} already exists, skipping duplicate save")
                return existing_result
            # Extract data from workflow state and serialize properly
            data = {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "workflow_mode": mode,
                "status": status,
                "current_stage": self._serialize_value(workflow_state.get("current_stage")),

                # Input data
                "user_input": workflow_state.get("user_input"),
                "input_type": workflow_state.get("input_type"),
                "source_name": workflow_state.get("source_name"),  # Add source name
                "raw_transaction_count": len(workflow_state.get("raw_transactions", [])),

                # Duplicate tracking - check if any transactions were flagged as duplicates
                "duplicates_detected": workflow_state.get("duplicates_found", 0),
                "duplicates_skipped": workflow_state.get("skipped", 0),

                # Classification results
                "predicted_category": workflow_state.get("predicted_category"),
                "category_confidence": workflow_state.get("category_confidence"),
                "transaction_type": self._extract_transaction_type(workflow_state),
                "transaction_type_confidence": workflow_state.get("transaction_type_confidence"),

                # Merchant extraction (NER) results
                "merchant_name": self._extract_merchant_name(workflow_state),
                "merchant_standardized": self._extract_standardized_merchant(workflow_state),
                "merchant_category": self._extract_merchant_category(workflow_state),
                "is_merchant_known": workflow_state.get("is_merchant_known", False),
                "merchant_confidence": workflow_state.get("merchant_confidence"),
                "extracted_entities": self._serialize_dict(workflow_state.get("ner_entities", {})) if workflow_state.get("ner_entities") else None,

                # Pattern analysis results
                "spending_patterns": self._format_spending_patterns(workflow_state),
                "pattern_insights": self._format_pattern_insights(workflow_state),
                "pattern_confidence": workflow_state.get("pattern_confidence"),

                # Suggestions and recommendations - serialize to handle Pydantic models
                # Note: Don't use truthiness check for lists, check for None explicitly
                "budget_recommendations": self._serialize_list(workflow_state.get("budget_recommendations", [])) if workflow_state.get("budget_recommendations") is not None else None,
                "spending_suggestions": self._serialize_list(workflow_state.get("spending_suggestions", [])) if workflow_state.get("spending_suggestions") is not None else None,
                "suggestion_confidence": workflow_state.get("suggestion_confidence"),
                "savings_opportunities": self._serialize_list(workflow_state.get("savings_opportunities", [])) if workflow_state.get("savings_opportunities") is not None else None,

                # Security and safety results - serialize to handle Pydantic models
                "security_alerts": self._serialize_list(workflow_state.get("security_alerts", [])) if workflow_state.get("security_alerts") is not None else None,
                "risk_assessment": self._serialize_dict(workflow_state.get("risk_assessment", {})) if workflow_state.get("risk_assessment") else None,
                "fraud_score": self._extract_fraud_score(workflow_state),
                "anomaly_score": self._extract_anomaly_score(workflow_state),
                "safety_confidence": workflow_state.get("safety_confidence"),
                "requires_human_review": self._check_requires_review(workflow_state),

                # Validation results - serialize to handle Pydantic models
                "validation_errors": self._serialize_list(self._format_validation_errors(workflow_state)) if self._format_validation_errors(workflow_state) is not None else None,
                "data_quality_score": self._calculate_data_quality_score(workflow_state),
                "is_valid": workflow_state.get("is_valid", True),

                # Processing metadata - serialize to handle enums and dates
                "processing_history": self._serialize_list(workflow_state.get("processing_history", [])),
                "confidence_scores": self._serialize_list(workflow_state.get("confidence_scores", [])),
                "error_log": self._serialize_list(workflow_state.get("error_log", [])),
                "retry_count": workflow_state.get("retry_count", 0),

                # Performance metrics
                "total_processing_time": workflow_state.get("total_processing_time"),
                "stage_timings": self._serialize_dict(self._extract_stage_timings(workflow_state) or {}),

                # Final processed transaction - serialize to handle any enums
                "final_transaction": self._serialize_dict(workflow_state.get("final_transaction", {})) if workflow_state.get("final_transaction") else None,

                # Timestamps
                "started_at": self._format_timestamp(workflow_state.get("started_at")),
                "completed_at": self._format_timestamp(workflow_state.get("completed_at")),
            }

            # Final pass: serialize the entire data dict to catch any remaining non-serializable objects
            data = self._serialize_dict(data)

            # Insert into Supabase
            result = self.supabase.table("prediction_results").insert(data).execute()

            if result.data:
                logger.info(f"Saved prediction result for workflow {workflow_id}")
                return result.data[0]
            else:
                logger.error(f"Failed to save prediction result: {result}")
                return {}

        except Exception as e:
            logger.error(f"Error saving prediction result: {e}", exc_info=True)
            raise

    def update_prediction_result(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing prediction result

        Args:
            workflow_id: Workflow identifier
            updates: Fields to update

        Returns:
            Updated prediction result record
        """
        try:
            result = (
                self.supabase.table("prediction_results")
                .update(updates)
                .eq("workflow_id", workflow_id)
                .execute()
            )

            if result.data:
                logger.info(f"✅ Updated prediction result for workflow {workflow_id}")
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Error updating prediction result: {e}", exc_info=True)
            return None

    def get_prediction_result(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get prediction result by workflow ID"""
        try:
            result = (
                self.supabase.table("prediction_results")
                .select("*")
                .eq("workflow_id", workflow_id)
                .execute()
            )

            # Check if we have data and return the first result
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"❌ Error fetching prediction result: {e}")
            return None

    # Helper methods for data extraction and formatting

    def _serialize_value(self, value: Any) -> Any:
        """Serialize values that are not JSON serializable (enums, dates, Pydantic models, etc.)"""
        if value is None:
            return None

        # Handle Pydantic v2 models (convert to dict)
        if hasattr(value, 'model_dump'):
            try:
                return value.model_dump()
            except Exception:
                pass

        # Handle Pydantic v1 models
        if hasattr(value, 'dict') and callable(value.dict):
            try:
                return value.dict()
            except Exception:
                pass

        # Handle dataclass objects
        if hasattr(value, '__dataclass_fields__'):
            try:
                from dataclasses import asdict
                return asdict(value)
            except Exception:
                pass

        # Handle enum types - convert to their value
        if hasattr(value, 'value') and not isinstance(value, dict):
            try:
                return value.value
            except Exception:
                pass

        # Handle datetime objects
        if hasattr(value, 'isoformat') and callable(value.isoformat):
            try:
                return value.isoformat()
            except Exception:
                pass

        # Handle sets and tuples
        if isinstance(value, (set, tuple)):
            return list(value)

        # Return as-is if already serializable (str, int, float, bool, list, dict)
        return value

    def _serialize_list(self, items: list) -> list:
        """Recursively serialize a list of items"""
        if not items:
            return []

        result = []
        for item in items:
            if isinstance(item, dict):
                # Recursively serialize dict items
                result.append(self._serialize_dict(item))
            elif isinstance(item, list):
                # Recursively serialize nested lists
                result.append(self._serialize_list(item))
            else:
                # Serialize individual values
                result.append(self._serialize_value(item))

        return result

    def _serialize_dict(self, data: dict) -> dict:
        """Recursively serialize a dictionary"""
        if not data:
            return {}

        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._serialize_dict(value)
            elif isinstance(value, list):
                result[key] = self._serialize_list(value)
            else:
                result[key] = self._serialize_value(value)

        return result

    def _extract_merchant_name(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract merchant name from NER entities, merchant info, or final transaction"""
        # Try merchant_info first
        merchant_info = state.get("merchant_info", {})
        if merchant_info and isinstance(merchant_info, dict):
            name = merchant_info.get("name") or merchant_info.get("merchant_name")
            if name:
                return name

        # Try NER entities
        ner_entities = state.get("ner_entities", {})
        if ner_entities and isinstance(ner_entities, dict):
            merchants = ner_entities.get("merchants", [])
            if merchants and len(merchants) > 0:
                return merchants[0].get("value") if isinstance(merchants[0], dict) else str(merchants[0])

        # Fallback: check final_transaction or preprocessed_data
        final_transaction = state.get("final_transaction", {})
        if final_transaction and isinstance(final_transaction, dict):
            # Check preprocessed_data inside final_transaction
            preprocessed = final_transaction.get("preprocessed_data", {})
            if preprocessed and isinstance(preprocessed, dict):
                merchant = preprocessed.get("merchant_name")
                if merchant:
                    return merchant

            # Check top-level merchant_name in final_transaction
            merchant = final_transaction.get("merchant_name")
            if merchant:
                return merchant

        # Last fallback: check processed_transactions
        processed = state.get("processed_transactions", [])
        if processed and len(processed) > 0:
            first_txn = processed[0]
            if isinstance(first_txn, dict):
                merchant = first_txn.get("merchant_name")
                if merchant:
                    return merchant

        return None

    def _extract_standardized_merchant(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract standardized merchant name"""
        merchant_info = state.get("merchant_info", {})
        if merchant_info and isinstance(merchant_info, dict):
            return merchant_info.get("standardized_name") or merchant_info.get("standardized")
        return None

    def _format_spending_patterns(self, state: Dict[str, Any]) -> Optional[list]:
        """Format spending patterns for storage"""
        patterns = state.get("spending_patterns")

        if not patterns:
            return None

        # If already a list, return as is
        if isinstance(patterns, list):
            return patterns

        # If it's a dict, try to convert to list
        if isinstance(patterns, dict):
            try:
                result = []
                for k, v in patterns.items():
                    if isinstance(v, dict):
                        result.append({"pattern_type": k, **v})
                    else:
                        result.append({"pattern_type": k, "value": v})
                return result if result else None
            except Exception as e:
                logger.warning(f"Could not format spending_patterns: {e}")
                # Return the dict as-is wrapped in a list
                return [patterns]

        return None

    def _format_pattern_insights(self, state: Dict[str, Any]) -> Optional[list]:
        """Format pattern insights for storage"""
        insights = state.get("pattern_insights")

        if not insights:
            return None

        # If already a list, return as is
        if isinstance(insights, list):
            return insights

        # If it's a dict, convert to list
        if isinstance(insights, dict):
            try:
                # If dict has numeric keys, extract values
                if all(str(k).isdigit() for k in insights.keys()):
                    return list(insights.values())
                # Otherwise wrap the dict
                return [insights]
            except Exception as e:
                logger.warning(f"Could not format pattern_insights: {e}")
                return [insights]

        return None

    def _extract_fraud_score(self, state: Dict[str, Any]) -> Optional[float]:
        """Extract fraud score from risk assessment"""
        risk_assessment = state.get("risk_assessment", {})
        if risk_assessment and isinstance(risk_assessment, dict):
            return risk_assessment.get("fraud_score")
        return None

    def _extract_anomaly_score(self, state: Dict[str, Any]) -> Optional[float]:
        """Extract anomaly score from risk assessment"""
        risk_assessment = state.get("risk_assessment", {})
        if risk_assessment and isinstance(risk_assessment, dict):
            return risk_assessment.get("anomaly_score")
        return None

    def _check_requires_review(self, state: Dict[str, Any]) -> bool:
        """Check if prediction requires human review"""
        # Check validation errors
        validation_errors = state.get("validation_errors", [])
        if validation_errors:
            return True

        # Check confidence scores
        category_confidence = state.get("category_confidence", 1.0)
        if category_confidence < 0.5:
            return True

        # Check risk scores
        risk_assessment = state.get("risk_assessment", {})
        if risk_assessment:
            fraud_score = risk_assessment.get("fraud_score", 0)
            anomaly_score = risk_assessment.get("anomaly_score", 0)
            if fraud_score > 0.7 or anomaly_score > 0.7:
                return True

        return False

    def _format_validation_errors(self, state: Dict[str, Any]) -> Optional[list]:
        """Format validation errors for storage"""
        errors = state.get("validation_errors", [])
        if not errors:
            return None

        # Convert string errors to structured format
        formatted_errors = []
        for error in errors:
            if isinstance(error, str):
                formatted_errors.append({
                    "field": "unknown",
                    "error": error,
                    "severity": "error"
                })
            elif isinstance(error, dict):
                formatted_errors.append(error)

        return formatted_errors if formatted_errors else None

    def _calculate_data_quality_score(self, state: Dict[str, Any]) -> Optional[float]:
        """Calculate overall data quality score"""
        data_quality_scores = state.get("data_quality_scores", {})
        if data_quality_scores and isinstance(data_quality_scores, dict):
            scores = [v for v in data_quality_scores.values() if isinstance(v, (int, float))]
            return sum(scores) / len(scores) if scores else None
        return None

    def _extract_stage_timings(self, state: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract stage timings from processing history"""
        processing_history = state.get("processing_history", [])
        if not processing_history:
            return None

        timings = {}
        for entry in processing_history:
            if isinstance(entry, dict):
                stage = entry.get("stage")
                duration = entry.get("duration_ms") or entry.get("duration")
                if stage and duration:
                    timings[stage] = duration

        return timings if timings else None

    def _format_timestamp(self, timestamp: Any) -> Optional[str]:
        """Format timestamp for PostgreSQL"""
        if not timestamp:
            return None

        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        else:
            return str(timestamp)

    def _extract_transaction_type(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract transaction type from state, final_transaction, or processed_transactions"""
        # Try direct field first
        txn_type = state.get("transaction_type")
        if txn_type:
            return txn_type

        # Check final_transaction
        final_transaction = state.get("final_transaction", {})
        if final_transaction and isinstance(final_transaction, dict):
            # Check preprocessed_data inside final_transaction
            preprocessed = final_transaction.get("preprocessed_data", {})
            if preprocessed and isinstance(preprocessed, dict):
                txn_type = preprocessed.get("transaction_type")
                if txn_type:
                    return txn_type

            # Check top-level transaction_type in final_transaction
            txn_type = final_transaction.get("transaction_type")
            if txn_type:
                return txn_type

        # Check processed_transactions
        processed = state.get("processed_transactions", [])
        if processed and len(processed) > 0:
            first_txn = processed[0]
            if isinstance(first_txn, dict):
                txn_type = first_txn.get("transaction_type")
                if txn_type:
                    return txn_type

        return None

    def _extract_merchant_category(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract merchant category from merchant_info or NER"""
        # Try direct field first
        category = state.get("merchant_category")
        if category:
            return category

        # Try merchant_info
        merchant_info = state.get("merchant_info", {})
        if merchant_info and isinstance(merchant_info, dict):
            category = merchant_info.get("category")
            if category:
                return category

        # Try predicted_category as fallback
        return state.get("predicted_category")


# Singleton instance
_prediction_results_service: Optional[PredictionResultsService] = None


def get_prediction_results_service() -> PredictionResultsService:
    """Get or create the singleton prediction results service"""
    global _prediction_results_service
    if _prediction_results_service is None:
        _prediction_results_service = PredictionResultsService()
    return _prediction_results_service
