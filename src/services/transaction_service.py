"""
Transaction Service - Enhanced implementation with Database Persistence
Handles transaction processing with UnifiedWorkflow AND database storage
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import pandas as pd
from ..models.transaction import Transaction, TransactionCreate, TransactionResponse
from ..db.operations import TransactionCRUD

class TransactionService:
    """Enhanced transaction service with database persistence"""

    def __init__(self, db):
        self.db = db

    async def process_uploaded_transactions(self, df: pd.DataFrame, user_id: str) -> Dict[str, int]:
        """Process uploaded transaction file through the unified workflow pipeline AND save to database"""
        from ..agents.ingestion_agent import EnhancedIngestionAgent, IngestionAgentInput
        from ..workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode

        try:
            # Initialize enhanced ingestion agent
            ingestion_agent = EnhancedIngestionAgent()

            # Process through enhanced ingestion agent first
            input_data = IngestionAgentInput(
                input_type="structured",
                dataframe=df
            )
            ingestion_result = ingestion_agent.process(input_data)

            if ingestion_result.status == "success" and ingestion_result.preprocessed_transactions:
                # Convert processed transactions to database records
                saved_count = 0
                for transaction_data in ingestion_result.preprocessed_transactions:
                    try:
                        # Prepare data for database insertion
                        db_data = {
                            "user_id": user_id,
                            "amount": transaction_data.get("amount", 0.0),
                            "description": transaction_data.get("description", ""),
                            "date": transaction_data.get("date", datetime.now()),
                            "merchant": transaction_data.get("merchant"),
                            "category": transaction_data.get("category"),
                            "subcategory": transaction_data.get("subcategory"),
                            "transaction_type": transaction_data.get("transaction_type", "debit"),
                            "status": "completed",
                            "processed_by_agent": "ingestion_agent",
                            "processing_version": "1.0"
                        }
                        
                        # Save to database
                        await TransactionCRUD.create_transaction(self.db, db_data)
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"⚠️ Failed to save transaction: {e}")
                        continue

                print(f"✅ Saved {saved_count} transactions to database")
                return {
                    "total": len(df),
                    "processed": len(ingestion_result.preprocessed_transactions),
                    "saved_to_db": saved_count,
                    "skipped": len(df) - len(ingestion_result.preprocessed_transactions),
                    "errors": len(ingestion_result.errors)
                }
            else:
                print(f"❌ Preprocessing failed: {ingestion_result.error}")
                return {
                    "total": len(df),
                    "processed": 0,
                    "saved_to_db": 0,
                    "skipped": len(df),
                    "errors": 1
                }
                
        except Exception as e:
            print(f"❌ Upload processing failed: {e}")
            return {
                "total": len(df),
                "processed": 0,
                "saved_to_db": 0,
                "skipped": len(df),
                "errors": 1
            }

    async def create_transaction(self, transaction_data: Dict[str, Any]) -> TransactionResponse:
        """Create a single transaction and save to database"""
        try:
            # Create transaction in database
            db_transaction = await TransactionCRUD.create_transaction(self.db, transaction_data)
            
            # Convert to response format
            return TransactionResponse(**db_transaction.to_dict())
            
        except Exception as e:
            raise ValueError(f"Failed to create transaction: {str(e)}")

    async def get_transaction(self, transaction_id: str, user_id: str) -> Optional[TransactionResponse]:
        """Get a specific transaction from database"""
        db_transaction = await TransactionCRUD.get_transaction(self.db, transaction_id, user_id)
        
        if db_transaction:
            return TransactionResponse(**db_transaction.to_dict())
        return None

    async def get_transactions(self, filters: Dict[str, Any]) -> Tuple[List[TransactionResponse], int]:
        """Get transactions from database with filtering and pagination"""
        db_transactions, total = await TransactionCRUD.get_transactions(self.db, filters)
        
        transactions = [TransactionResponse(**t.to_dict()) for t in db_transactions]
        return transactions, total

    async def update_transaction(self, transaction_id: str, update_data: Dict[str, Any]) -> Optional[TransactionResponse]:
        """Update a transaction in database"""
        db_transaction = await TransactionCRUD.update_transaction(self.db, transaction_id, update_data)
        
        if db_transaction:
            return TransactionResponse(**db_transaction.to_dict())
        return None

    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction from database"""
        return await TransactionCRUD.delete_transaction(self.db, transaction_id)

    async def batch_create_transactions(self, transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple transactions in database"""
        return await TransactionCRUD.batch_create_transactions(self.db, transactions_data)

    async def verify_transaction_ownership(self, transaction_ids: List[str], user_id: str) -> List:
        """Verify transaction ownership"""
        return await TransactionCRUD.verify_transaction_ownership(self.db, transaction_ids, user_id)

    async def batch_update_transactions(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch update transactions"""
        updated = 0
        failed = 0
        errors = []
        
        for update in updates:
            try:
                transaction_id = update["id"]
                update_data = update["data"]
                
                result = await self.update_transaction(transaction_id, update_data)
                if result:
                    updated += 1
                else:
                    failed += 1
                    errors.append(f"Transaction {transaction_id} not found")
                    
            except Exception as e:
                failed += 1
                errors.append(f"Transaction {update.get('id', 'unknown')}: {str(e)}")
        
        return {
            "updated": updated,
            "failed": failed,
            "errors": errors
        }

    async def batch_delete_transactions(self, transaction_ids: List[str]) -> Dict[str, Any]:
        """Batch delete transactions"""
        deleted = 0
        failed = 0
        errors = []
        
        for transaction_id in transaction_ids:
            try:
                success = await self.delete_transaction(transaction_id)
                if success:
                    deleted += 1
                else:
                    failed += 1
                    errors.append(f"Transaction {transaction_id} not found")
                    
            except Exception as e:
                failed += 1
                errors.append(f"Transaction {transaction_id}: {str(e)}")
        
        return {
            "deleted": deleted,
            "failed": failed,
            "errors": errors
        }

    async def get_transaction_summary(self, user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get transaction summary from database"""
        return await TransactionCRUD.get_transaction_summary(self.db, user_id, start_date, end_date)

    async def process_natural_language_transaction(
        self,
        text: str,
        user_id: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process natural language transaction input through unified workflow"""
        from ..workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode

        try:
            # Initialize unified workflow
            workflow = UnifiedTransactionWorkflow()

            # Execute workflow with quick classification mode for conversational input
            result = await workflow.execute_workflow(
                mode=WorkflowMode.QUICK_CLASSIFICATION,
                user_input=text,
                user_id=user_id
            )

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "message": "Transaction processed successfully",
                    "workflow_id": result.get("workflow_id"),
                    "execution_time": result.get("execution_time"),
                    "extracted_data": result.get("result", {}),
                    "conversation_id": conversation_context.get("conversation_id") if conversation_context else None
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to process transaction",
                    "error": result.get("error", "Unknown error")
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Transaction processing failed: {str(e)}"
            }

    async def get_transaction_suggestions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get transaction suggestions for a user"""
        # Mock implementation - replace with actual database queries
        suggestions = [
            {
                "id": f"suggestion_{i}",
                "type": "category_suggestion",
                "message": f"Consider categorizing similar transactions as 'Dining Out'",
                "confidence": 0.85,
                "created_at": datetime.utcnow().isoformat()
            }
            for i in range(min(limit, 3))
        ]
        return suggestions

    async def get_transaction_insights(self, user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get transaction insights and analytics"""
        # Mock implementation - replace with actual analytics
        return {
            "period": period,
            "total_transactions": 45,
            "total_amount": 1250.50,
            "top_categories": [
                {"category": "Dining", "amount": 450.25, "count": 15},
                {"category": "Groceries", "amount": 320.75, "count": 12},
                {"category": "Transportation", "amount": 180.50, "count": 8}
            ],
            "spending_trend": "increasing",
            "anomalies_detected": 2,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def validate_transaction_data(self, transaction_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate transaction data"""
        errors = []

        # Basic validation
        if not transaction_data.get("description"):
            errors.append("Description is required")

        if not transaction_data.get("amount"):
            errors.append("Amount is required")
        elif not isinstance(transaction_data["amount"], (int, float)):
            errors.append("Amount must be a number")

        if not transaction_data.get("date"):
            errors.append("Date is required")

        return len(errors) == 0, errors

    async def batch_process_transactions(
        self,
        transactions: List[Dict[str, Any]],
        user_id: str,
        mode: str = "full_pipeline"
    ) -> Dict[str, Any]:
        """Process multiple transactions in batch through unified workflow"""
        from ..workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode

        try:
            # Convert mode string to WorkflowMode enum
            try:
                workflow_mode = WorkflowMode(mode)
            except ValueError:
                workflow_mode = WorkflowMode.FULL_PIPELINE

            workflow = UnifiedTransactionWorkflow()
            results = []

            for i, transaction in enumerate(transactions):
                try:
                    # Validate transaction data
                    is_valid, validation_errors = await self.validate_transaction_data(transaction)

                    if not is_valid:
                        results.append({
                            "index": i,
                            "status": "error",
                            "errors": validation_errors
                        })
                        continue

                    # Process through workflow
                    result = await workflow.execute_workflow(
                        mode=workflow_mode,
                        user_input=transaction.get("description", ""),
                        user_id=user_id,
                        amount=transaction.get("amount"),
                        date=transaction.get("date"),
                        merchant=transaction.get("merchant")
                    )

                    results.append({
                        "index": i,
                        "status": result["status"],
                        "workflow_id": result.get("workflow_id"),
                        "execution_time": result.get("execution_time")
                    })

                except Exception as e:
                    results.append({
                        "index": i,
                        "status": "error",
                        "error": str(e)
                    })

            success_count = sum(1 for r in results if r["status"] == "success")

            return {
                "status": "completed",
                "total_transactions": len(transactions),
                "successful_transactions": success_count,
                "failed_transactions": len(transactions) - success_count,
                "results": results,
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Batch processing failed: {str(e)}",
                "processed_at": datetime.utcnow().isoformat()
            }
