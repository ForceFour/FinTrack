"""
Transaction Service - Enhanced implementation with Database Persistence
Handles transaction processing with UnifiedWorkflow AND database storage
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timezone
import pandas as pd
from supabase import Client
from ..models.transaction import Transaction, TransactionCreate, TransactionResponse
from ..db.operations import TransactionCRUD


class TransactionService:
    """Enhanced transaction service with database persistence"""

    def __init__(self, client: Client):
        self.client = client

    def _map_db_to_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map database enum values to Pydantic response values"""
        mapped = data.copy()

        # Map transaction_type
        if mapped.get('transaction_type') == 'debit':
            mapped['transaction_type'] = 'expense'
        elif mapped.get('transaction_type') == 'credit':
            mapped['transaction_type'] = 'income'

        # Map status
        if mapped.get('status') == 'completed':
            mapped['status'] = 'processed'

        # Convert date string to date object if needed
        if isinstance(mapped.get('date'), str):
            from datetime import datetime
            try:
                # Try parsing as ISO format
                mapped['date'] = datetime.fromisoformat(mapped['date'].replace('Z', '+00:00')).date()
            except:
                # If parsing fails, keep as string
                pass

        return mapped

    async def process_uploaded_transactions(self, df: pd.DataFrame, user_id: str) -> Dict[str, int]:
        """Process uploaded transaction file through the unified workflow pipeline AND save to database"""
        from ..agents.ingestion_agent import IngestionAgent, IngestionAgentInput
        from ..workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode

        try:
            # Filter out duplicates before processing
            df_filtered, duplicates_found = await self._filter_duplicates_from_df(df, user_id)

            # If no transactions left after filtering, return early
            if df_filtered.empty:
                return {
                    "total": len(df),
                    "processed": 0,
                    "saved_to_db": 0,
                    "skipped": duplicates_found,
                    "errors": 0
                }

            # Initialize enhanced ingestion agent for initial preprocessing
            ingestion_agent = IngestionAgent()

            # Process through enhanced ingestion agent first
            input_data = IngestionAgentInput(
                input_type="structured",
                dataframe=df_filtered
            )
            ingestion_result = ingestion_agent.process(input_data)

            if ingestion_result.metadata.get("status") == "completed" and ingestion_result.preprocessed_transactions:
                # Convert to raw transaction format for unified workflow
                raw_transactions = []
                for transaction in ingestion_result.preprocessed_transactions:
                    raw_transactions.append({
                        "date": transaction.date.isoformat(),
                        "amount": transaction.amount,
                        "description": transaction.description_cleaned,
                        "transaction_type": transaction.transaction_type.value if hasattr(transaction.transaction_type, 'value') else str(transaction.transaction_type),
                        "payment_method": transaction.payment_method.value if hasattr(transaction.payment_method, 'value') else str(transaction.payment_method),
                        "category": transaction.metadata.get('original_category', ''),
                        "merchant": transaction.metadata.get('original_merchant', ''),
                    })

                # Get current transaction count BEFORE running workflow
                # This ensures suggestion agent knows if user has existing transactions
                current_transaction_count = await self.get_user_transaction_count(user_id)
                user_preferences = {
                    'transaction_count': current_transaction_count,
                    'has_existing_data': current_transaction_count > 0
                }

                # Now run the full unified workflow for merchant/category classification
                workflow = UnifiedTransactionWorkflow()
                workflow_result = await workflow.execute_workflow(
                    mode=WorkflowMode.FULL_PIPELINE,
                    raw_transactions=raw_transactions,
                    user_id=user_id,
                    conversation_context={
                        'user_preferences': user_preferences
                    }
                )

                if 'result' in workflow_result:
                    processed_txns = workflow_result['result'].get('processed_transactions', [])

                if workflow_result.get("status") == "success" and workflow_result.get("result", {}).get("processed_transactions"):
                    # Now save the fully processed transactions to database
                    saved_count = 0
                    for transaction_data in workflow_result["result"]["processed_transactions"]:
                        try:
                            # Check if this transaction is a duplicate
                            is_duplicate = await self._is_duplicate_transaction(transaction_data, user_id)
                            print(f"Checking duplicate for processed transaction: {transaction_data.description_cleaned}, amount: {transaction_data.amount}, duplicate: {is_duplicate}")
                            if is_duplicate:
                                continue  # Skip duplicates

                            # Prepare data for database insertion with merchant and category
                            db_data = {
                                "user_id": user_id,
                                "amount": transaction_data.amount,
                                "description": transaction_data.description_cleaned,
                                "date": transaction_data.date.isoformat() if hasattr(transaction_data.date, 'isoformat') else str(transaction_data.date),
                                "merchant": getattr(transaction_data, 'merchant_name', None) or getattr(transaction_data, 'merchant', None),
                                "category": transaction_data.predicted_category.value if hasattr(transaction_data.predicted_category, 'value') else str(getattr(transaction_data, 'predicted_category', getattr(transaction_data, 'category', 'miscellaneous'))),
                                "transaction_type": transaction_data.transaction_type.value if hasattr(transaction_data.transaction_type, 'value') else str(transaction_data.transaction_type),
                                "payment_method": transaction_data.payment_method.value if hasattr(transaction_data.payment_method, 'value') else str(transaction_data.payment_method),
                                "status": "completed"
                            }

                            print(f"Saving processed transaction: {db_data}")
                            # Save to database
                            await TransactionCRUD.create_transaction(self.client, db_data)
                            saved_count += 1

                        except Exception as e:
                            print(f"Error saving processed transaction: {e}")
                            continue

                    print(f"Saved {saved_count} processed transactions to database")

                    total_processed = len(workflow_result["result"]["processed_transactions"])
                    return {
                        "total": len(df),
                        "processed": total_processed,
                        "saved_to_db": saved_count,
                        "skipped": duplicates_found,
                        "errors": 0
                    }
                else:
                    print("Going to fallback path")
                    # Fallback: try to save preprocessed transactions
                    saved_count = 0
                    for transaction_data in ingestion_result.preprocessed_transactions:
                        try:
                            # Check if this transaction is a duplicate before saving
                            is_duplicate = await self._is_duplicate_transaction(transaction_data, user_id)
                            if is_duplicate:
                                continue  # Skip duplicates

                            # Prepare data for database insertion
                            db_data = {
                                "user_id": user_id,
                                "amount": transaction_data.amount,
                                "description": transaction_data.description_cleaned,
                                "date": transaction_data.date.isoformat() if hasattr(transaction_data.date, 'isoformat') else str(transaction_data.date),
                                "merchant": getattr(transaction_data, 'merchant_name', None),
                                "category": getattr(transaction_data, 'category', 'miscellaneous'),
                                "transaction_type": transaction_data.transaction_type.value if hasattr(transaction_data.transaction_type, 'value') else str(transaction_data.transaction_type),
                                "payment_method": transaction_data.payment_method.value if hasattr(transaction_data.payment_method, 'value') else str(transaction_data.payment_method),
                                "status": "completed"
                            }

                            # Save to database
                            await TransactionCRUD.create_transaction(self.client, db_data)
                            saved_count += 1

                        except Exception as e:
                            continue

                    total_processed = len(ingestion_result.preprocessed_transactions)
                    return {
                        "total": len(df),
                        "processed": total_processed,
                        "saved_to_db": saved_count,
                        "skipped": duplicates_found,
                        "errors": 1 if workflow_result.get("status") != "success" else 0
                    }
            else:
                error_msg = ingestion_result.metadata.get("error", "Unknown error")
                return {
                    "total": len(df),
                    "processed": 0,
                    "saved_to_db": 0,
                    "skipped": len(df),
                    "errors": 1
                }

        except Exception as e:
            return {
                "total": len(df),
                "processed": 0,
                "saved_to_db": 0,
                "skipped": len(df),
                "errors": 1
            }

    async def _check_for_duplicates(self, df: pd.DataFrame, user_id: str) -> int:
        """Check for duplicate transactions in the uploaded data and against existing database"""
        duplicates = 0
        seen_in_upload = set()

        # First check for duplicates within the uploaded data itself
        for _, row in df.iterrows():
            # Create a unique key based on date, amount, and description
            key = (
                str(row.get('date', '')),
                float(row.get('amount', 0)),
                str(row.get('description', '')).strip().lower()
            )

            if key in seen_in_upload:
                duplicates += 1
            else:
                seen_in_upload.add(key)

        # Also check against existing database transactions
        # This is a preliminary check - the full check happens during individual processing
        try:
            existing = self.client.table("transactions").select("date,amount,description").eq("user_id", user_id).execute()
            existing_keys = set()

            for tx in existing.data or []:
                key = (
                    str(tx.get('date', '')),
                    float(tx.get('amount', 0)),
                    str(tx.get('description', '')).strip().lower()
                )
                existing_keys.add(key)

            # Check uploaded data against existing database
            for _, row in df.iterrows():
                key = (
                    str(row.get('date', '')),
                    float(row.get('amount', 0)),
                    str(row.get('description', '')).strip().lower()
                )
                if key in existing_keys:
                    duplicates += 1

        except Exception as e:
            pass

        return duplicates

    async def _filter_duplicates_from_df(self, df: pd.DataFrame, user_id: str) -> tuple[pd.DataFrame, int]:
        """Filter out duplicate transactions from dataframe before processing"""
        try:
            # Get existing transactions for comparison
            existing = self.client.table("transactions").select("date,amount,description").eq("user_id", user_id).execute()
            existing_keys = set()

            for tx in existing.data or []:
                # Normalize date to YYYY-MM-DD format
                date_str = str(tx.get('date', '')).split('T')[0].split(' ')[0]
                key = (
                    date_str,
                    float(tx.get('amount', 0)),
                    str(tx.get('description', '')).strip().lower()
                )
                existing_keys.add(key)

            # Filter dataframe to remove duplicates
            filtered_rows = []
            duplicates_found = 0
            seen_in_upload = set()

            for _, row in df.iterrows():
                # Normalize date to YYYY-MM-DD format
                date_str = str(row.get('date', '')).split('T')[0].split(' ')[0]
                key = (
                    date_str,
                    float(row.get('amount', 0)),
                    str(row.get('description', '')).strip().lower()
                )

                # Check for duplicates within the uploaded data itself
                if key in seen_in_upload:
                    duplicates_found += 1
                    continue

                # Check against existing database transactions
                if key in existing_keys:
                    duplicates_found += 1
                    continue

                # Not a duplicate, keep it
                seen_in_upload.add(key)
                filtered_rows.append(row)

            # Create filtered dataframe
            if filtered_rows:
                df_filtered = pd.DataFrame(filtered_rows)
            else:
                df_filtered = pd.DataFrame(columns=df.columns)

            return df_filtered, duplicates_found

        except Exception as e:
            # Return original dataframe if filtering fails
            return df, 0

    async def _is_duplicate_transaction(self, transaction_data, user_id: str) -> bool:
        """Check if a transaction already exists in the database"""
        try:
            # Query for existing transactions with similar characteristics
            existing = self.client.table("transactions").select("*").eq("user_id", user_id).execute()

            # Normalize the new transaction data - handle both dict and object
            if isinstance(transaction_data, dict):
                new_amount = transaction_data.get('amount', 0)
                new_date_str = transaction_data.get('date')
                if new_date_str and isinstance(new_date_str, str) and 'T' in new_date_str:
                    new_date_str = new_date_str.split('T')[0]
                new_desc = transaction_data.get('description_cleaned', transaction_data.get('description', '')).strip().lower()
                new_merchant = (transaction_data.get('merchant_name') or transaction_data.get('merchant', '')).strip().lower()
            else:
                # Handle object attributes
                new_amount = transaction_data.amount
                new_date_str = transaction_data.date.date().isoformat() if hasattr(transaction_data.date, 'date') else str(transaction_data.date).split(' ')[0]
                new_desc = transaction_data.description_cleaned.strip().lower()
                new_merchant = (getattr(transaction_data, 'merchant_name', '') or getattr(transaction_data, 'merchant', '')).strip().lower()

            for existing_tx in existing.data or []:
                # Check multiple criteria for duplicates:
                # 1. Exact amount match
                amount_match = abs(existing_tx['amount'] - new_amount) < 0.01

                # 2. Date match (normalize to YYYY-MM-DD format)
                existing_date_str = str(existing_tx['date']).split('T')[0].split(' ')[0]
                date_match = existing_date_str == new_date_str

                # 3. Description similarity (case-insensitive, strip whitespace)
                existing_desc = existing_tx['description'].strip().lower()
                desc_match = existing_desc == new_desc

                # 4. Merchant match (if available)
                existing_merchant = existing_tx.get('merchant', '').strip().lower()
                merchant_match = existing_merchant == new_merchant and existing_merchant != ''

                # Check for duplicates
                if amount_match and date_match:
                    if desc_match:
                        return True
                    if merchant_match:
                        return True
                    # For high-value transactions, be more strict
                    if abs(new_amount) > 1000:
                        return True

            return False
        except Exception as e:
            # In case of error, don't block the transaction
            return False

    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single transaction and save to database"""
        try:
            # Create transaction in database
            db_transaction = await TransactionCRUD.create_transaction(self.client, transaction_data)

            # Return the raw database response instead of trying to map to TransactionResponse
            # to avoid Pydantic validation issues
            return db_transaction

        except Exception as e:
            raise ValueError(f"Failed to create transaction: {str(e)}")

    async def get_transaction(self, transaction_id: str, user_id: str) -> Optional[TransactionResponse]:
        """Get a specific transaction from database"""
        db_transaction = await TransactionCRUD.get_transaction(self.client, transaction_id, user_id)

        if db_transaction:
            response_data = self._map_db_to_response(db_transaction)
            return TransactionResponse(**response_data)
        return None

    async def get_transactions(self, filters: Dict[str, Any]) -> Tuple[List[TransactionResponse], int]:
        """Get transactions from database with filtering and pagination"""
        db_transactions, total = await TransactionCRUD.get_transactions(self.client, filters)

        transactions = []
        for t in db_transactions:
            response_data = self._map_db_to_response(t)
            transactions.append(TransactionResponse(**response_data))
        return transactions, total

    async def update_transaction(self, transaction_id: str, update_data: Dict[str, Any]) -> Optional[TransactionResponse]:
        """Update a transaction in database"""
        db_transaction = await TransactionCRUD.update_transaction(self.client, transaction_id, update_data)

        if db_transaction:
            response_data = self._map_db_to_response(db_transaction)
            return TransactionResponse(**response_data)
        return None

    async def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction from database"""
        return await TransactionCRUD.delete_transaction(self.client, transaction_id)

    async def batch_create_transactions(self, transactions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple transactions in database"""
        return await TransactionCRUD.batch_create_transactions(self.client, transactions_data)

    async def verify_transaction_ownership(self, transaction_ids: List[str], user_id: str) -> List:
        """Verify transaction ownership"""
        return await TransactionCRUD.verify_transaction_ownership(self.client, transaction_ids, user_id)

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
        return await TransactionCRUD.get_transaction_summary(self.client, user_id, start_date, end_date)

    async def get_user_transaction_count(self, user_id: str) -> int:
        """Get total number of transactions for a user (all time, not just recent)"""
        try:
            # Query database directly for accurate count
            result = self.client.table("transactions").select("id", count="exact").eq("user_id", user_id).execute()
            total_count = result.count if hasattr(result, 'count') else len(result.data or [])
            print(f"Transaction count for user {user_id}: {total_count}")
            return total_count
        except Exception as e:
            print(f"Error getting transaction count for user {user_id}: {e}")
            return 0

    async def get_user_spending_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive spending profile for a user to inform suggestions"""
        try:
            # Get recent transaction summary (last 3 months)
            from datetime import datetime, timedelta
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)

            summary = await self.get_transaction_summary(user_id, start_date, end_date)
            transaction_count = await self.get_user_transaction_count(user_id)

            # Get recent transactions to analyze spending patterns
            filters = {
                "user_id": user_id,
                "limit": 50,  # Last 50 transactions for pattern analysis
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            recent_transactions, _ = await self.get_transactions(filters)

            return {
                "total_transactions": transaction_count,
                "recent_summary": summary,
                "recent_transactions": [t.dict() for t in recent_transactions],
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": 90
                }
            }
        except Exception as e:
            print(f"Error getting spending profile for user {user_id}: {e}")
            return {
                "total_transactions": 0,
                "recent_summary": {},
                "recent_transactions": [],
                "analysis_period": None
            }

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
