"""
Backend API Routes - Transaction Management
Handles all transaction-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import io
import json
import logging

from ..models.transaction import Transaction, TransactionCreate, TransactionUpdate, TransactionResponse
from ..models.user import User
from ..services.transaction_service import TransactionService
# from ..services.auth_service import get_current_user  # Temporarily disabled during migration
from ..core.database_config import get_db_client

# Temporary dummy user for testing during migration
async def get_current_user():
    """Temporary dummy user function during migration"""
    from datetime import datetime
    import uuid
    return User(
        id="e6afed5f-6e3b-4349-8526-0fc2d9658915",  # Use existing profile ID
        email="duwaragie22@gmail.com",
        username="testuser",
        hashed_password="dummy_hash",
        created_at=datetime.now()
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/upload", response_model=Dict[str, Any])
async def upload_transactions(
    file: UploadFile = File(...),
    file_type: str = "csv",
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Upload and process transaction file
    Supports CSV, Excel, and OFX formats
    """
    try:
        # Validate file type
        allowed_types = ["csv", "excel", "xlsx", "ofx"]
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {allowed_types}"
            )

        # Read file content
        file_content = await file.read()

        # Initialize transaction service
        transaction_service = TransactionService(client)

        # Process file based on type
        if file_type == "csv":
            df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
        elif file_type in ["excel", "xlsx"]:
            df = pd.read_excel(io.BytesIO(file_content))
        elif file_type == "ofx":
            # OFX parsing would need specialized library (ofxparse)
            raise HTTPException(
                status_code=400,
                detail="OFX file support coming soon"
            )

        # Validate required columns
        required_columns = ["date", "amount", "description"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )

        # Process transactions
        result = await transaction_service.process_uploaded_transactions(
            df, user.id
        )

        return {
            "status": "success",
            "message": "File processed successfully",
            "transactions_processed": result["total"],
            "new_transactions": result["saved_to_db"],
            "duplicates_found": result["skipped"],
            "errors": result.get("errors", 0)
        }

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="File is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")

@router.get("/", response_model=Dict[str, Any])
async def get_transactions(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(default=None),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    min_amount: Optional[float] = Query(default=None),
    max_amount: Optional[float] = Query(default=None),
    search: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Get transactions with filtering and pagination
    """
    try:
        transaction_service = TransactionService(client)

        # Build filters
        filters = {
            "user_id": user.id,
            "limit": limit,
            "offset": offset
        }

        if category:
            filters["category"] = category
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_amount is not None:
            filters["min_amount"] = min_amount
        if max_amount is not None:
            filters["max_amount"] = max_amount
        if search:
            filters["search"] = search

        transactions, total = await transaction_service.get_transactions(filters)

        return {
            "transactions": [transaction.dict() for transaction in transactions],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Create a new transaction
    """
    try:
        transaction_service = TransactionService(client)

        # Add user ID to transaction
        transaction_data = transaction.dict()
        transaction_data["user_id"] = user.id

        created_transaction = await transaction_service.create_transaction(transaction_data)

        return created_transaction

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Get a specific transaction
    """
    try:
        transaction_service = TransactionService(client)

        transaction = await transaction_service.get_transaction(transaction_id, user.id)

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return transaction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_update: TransactionUpdate,
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Update a transaction
    """
    try:
        transaction_service = TransactionService(client)

        # Verify transaction exists and belongs to user
        existing_transaction = await transaction_service.get_transaction(transaction_id, user.id)
        if not existing_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        updated_transaction = await transaction_service.update_transaction(
            transaction_id, transaction_update.dict(exclude_unset=True)
        )

        return updated_transaction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Delete a transaction
    """
    try:
        transaction_service = TransactionService(client)

        # Verify transaction exists and belongs to user
        existing_transaction = await transaction_service.get_transaction(transaction_id, user.id)
        if not existing_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        success = await transaction_service.delete_transaction(transaction_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete transaction")

        return {"status": "success", "message": "Transaction deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=Dict[str, Any])
async def batch_create_transactions(
    transactions: List[TransactionCreate],
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Create multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(client)

        # Add user ID to all transactions
        transactions_data = []
        for transaction in transactions:
            transaction_data = transaction.dict()
            transaction_data["user_id"] = user.id
            transactions_data.append(transaction_data)

        result = await transaction_service.batch_create_transactions(transactions_data)

        return {
            "status": "success",
            "message": "Batch operation completed",
            "created": result["created"],
            "failed": result["failed"],
            "errors": result.get("errors", [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/batch", response_model=Dict[str, Any])
async def batch_update_transactions(
    updates: List[Dict[str, Any]],  # List of {id: str, data: dict}
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Update multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(client)

        # Validate that all transactions belong to user
        transaction_ids = [update["id"] for update in updates]
        owned_transactions = await transaction_service.verify_transaction_ownership(
            transaction_ids, user.id
        )

        if len(owned_transactions) != len(transaction_ids):
            raise HTTPException(
                status_code=403,
                detail="Some transactions don't belong to the current user"
            )

        result = await transaction_service.batch_update_transactions(updates)

        return {
            "status": "success",
            "message": "Batch update completed",
            "updated": result["updated"],
            "failed": result["failed"],
            "errors": result.get("errors", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/batch", response_model=Dict[str, Any])
async def batch_delete_transactions(
    transaction_ids: List[str],
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Delete multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(client)

        # Validate that all transactions belong to user
        owned_transactions = await transaction_service.verify_transaction_ownership(
            transaction_ids, user.id
        )

        if len(owned_transactions) != len(transaction_ids):
            raise HTTPException(
                status_code=403,
                detail="Some transactions don't belong to the current user"
            )

        result = await transaction_service.batch_delete_transactions(transaction_ids)

        return {
            "status": "success",
            "message": "Batch delete completed",
            "deleted": result["deleted"],
            "failed": result["failed"],
            "errors": result.get("errors", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{format}")
async def export_transactions(
    format: str,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    category: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Export transactions in various formats (CSV, Excel, JSON)
    """
    try:
        if format not in ["csv", "excel", "json"]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use csv, excel, or json"
            )

        transaction_service = TransactionService(client)

        # Get all matching transactions (no limit for export)
        filters = {
            "user_id": user.id,
            "limit": 10000,  # Large number for export
            "offset": 0
        }

        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if category:
            filters["category"] = category

        transactions, _ = await transaction_service.get_transactions(filters)

        # Convert to DataFrame
        df = pd.DataFrame([transaction.dict() for transaction in transactions])

        if df.empty:
            raise HTTPException(status_code=404, detail="No transactions found for export")

        # Generate export based on format
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"

        elif format == "excel":
            output = io.BytesIO()
            df.to_excel(output, index=False)
            content = output.getvalue()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx"

        elif format == "json":
            content = df.to_json(orient="records", date_format="iso")
            media_type = "application/json"
            filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.json"

        return JSONResponse(
            content={"data": content, "filename": filename},
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/stats", response_model=Dict[str, Any])
async def get_transaction_summary(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Get transaction summary statistics
    """
    try:
        transaction_service = TransactionService(client)

        summary = await transaction_service.get_transaction_summary(
            user.id, start_date, end_date
        )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/natural-language", response_model=Dict[str, Any])
async def process_natural_language_transaction(
    request: Dict[str, Any],
    user: User = Depends(get_current_user),
    client = Depends(get_db_client)
):
    """
    Process natural language transaction input through conversational interface
    """
    try:
        user_input = request.get("user_input", "").strip()
        conversation_context = request.get("conversation_context", {})

        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")

        # Initialize transaction service
        transaction_service = TransactionService(client)

        # Parse the natural language input
        parsed_transactions = await _parse_natural_language_transaction(
            user_input, conversation_context, user.id, transaction_service
        )

        if not parsed_transactions:
            return {
                "status": "error",
                "response": "I couldn't identify any transactions in your message. Please try again with amounts and descriptions.",
                "conversation_context": conversation_context,
                "transaction_processed": False
            }

        # Check if we have all required information for all transactions
        required_fields = ["amount", "description", "date"]
        all_have_required = True
        missing_fields = set()

        for tx in parsed_transactions:
            for field in required_fields:
                if not tx.get(field):
                    all_have_required = False
                    missing_fields.add(field)

        if not all_have_required:
            # Ask for missing information conversationally
            response_text = await _generate_conversational_response(
                parsed_transactions[0], list(missing_fields), conversation_context
            )

            # Update conversation context
            updated_context = conversation_context.copy()
            updated_context.update({
                "pending_transactions": parsed_transactions,
                "missing_fields": list(missing_fields),
                "last_input": user_input
            })

            return {
                "status": "incomplete",
                "response": response_text,
                "conversation_context": updated_context,
                "transaction_processed": False,
                "needs_more_info": True,
                "missing_fields": list(missing_fields)
            }

        else:
            # All information available, create all transactions
            try:
                created_transactions = []
                for tx_data in parsed_transactions:
                    from datetime import datetime
                    db_data = {
                        "user_id": user.id,
                        "amount": tx_data["amount"],
                        "description": tx_data["description"],
                        "date": datetime.fromisoformat(tx_data["date"]) if isinstance(tx_data["date"], str) else tx_data["date"],
                        "merchant": tx_data.get("merchant"),
                        "category": tx_data.get("category"),
                        "transaction_type": "debit" if tx_data["amount"] < 0 else "credit",
                        "status": "completed"
                    }

                    created_tx = await transaction_service.create_transaction(db_data)
                    created_transactions.append(created_tx)

                # Generate response for multiple transactions
                response_lines = ["✅ Transactions recorded successfully!\n"]
                for i, tx in enumerate(created_transactions, 1):
                    response_lines.append(f"📝 Transaction {i}: {tx.description}")
                    # Show amount with sign and type indicator
                    amount_str = f"${abs(tx.amount):.2f}"
                    if tx.amount < 0:
                        response_lines.append(f"� Expense: -{amount_str}")
                    else:
                        response_lines.append(f"💰 Income: +{amount_str}")
                    response_lines.append(f"📅 {tx.date}")
                    if tx.merchant:
                        response_lines.append(f"🏪 {tx.merchant}")
                    if tx.category:
                        response_lines.append(f"📂 {tx.category}")
                    response_lines.append("")  # Empty line between transactions

                response_text = "\n".join(response_lines)
                response_text += "\nYou can view all your transactions in the Dashboard."

                return {
                    "status": "completed",
                    "response": response_text,
                    "conversation_context": {},
                    "transaction_processed": True,
                    "transaction_ids": [tx.id for tx in created_transactions],
                    "next_action": "View transactions in Dashboard or continue adding more transactions"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "response": f"Sorry, I couldn't save the transactions. Error: {str(e)}",
                    "conversation_context": conversation_context,
                    "transaction_processed": False
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natural language processing failed: {str(e)}")


async def _parse_natural_language_transaction(
    user_input: str,
    conversation_context: Dict[str, Any],
    user_id: str,
    transaction_service: TransactionService
) -> List[Dict[str, Any]]:
    """
    Parse natural language input to extract transaction information
    Returns a list of transaction dictionaries
    """
    import re
    from datetime import datetime, timedelta

    # Check if we have pending transactions that need completion
    pending_transactions = conversation_context.get("pending_transactions", [])
    if pending_transactions:
        # Try to extract date information from current input to complete pending transactions
        input_lower = user_input.lower().strip()

        # Check for date keywords
        today = datetime.now().date()
        provided_date = None

        if any(word in input_lower for word in ["today", "this morning", "this afternoon", "this evening"]):
            provided_date = today.isoformat()
        elif any(word in input_lower for word in ["yesterday"]):
            provided_date = (today - timedelta(days=1)).isoformat()
        elif "last" in input_lower and "week" in input_lower:
            provided_date = (today - timedelta(days=7)).isoformat()
        else:
            # Look for date patterns
            date_patterns = [
                r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)',  # 9th september
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            ]
            for pattern in date_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    try:
                        if r'(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)' in pattern:
                            # Day month format like "9th september"
                            day, month_name = match.groups()
                            day = int(day)
                            month_names = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }
                            month = month_names.get(month_name.lower())
                            if month:
                                year = datetime.now().year  # Assume current year
                                parsed_date = datetime(year, month, day).date()
                                provided_date = parsed_date.isoformat()
                                break
                        elif pattern.startswith(r'(\d{4})'):  # YYYY/MM/DD
                            year, month, day = map(int, match.groups())
                            parsed_date = datetime(year, month, day).date()
                            provided_date = parsed_date.isoformat()
                            break
                        else:  # Assume MM/DD/YYYY
                            month, day, year = map(int, match.groups())
                            parsed_date = datetime(year, month, day).date()
                            provided_date = parsed_date.isoformat()
                            break
                    except ValueError:
                        continue

        if provided_date:
            # Apply the date to all pending transactions
            completed_transactions = []
            for tx in pending_transactions:
                completed_tx = tx.copy()
                completed_tx["date"] = provided_date
                completed_transactions.append(completed_tx)
            return completed_transactions

    # Convert input to lowercase for easier matching
    input_lower = user_input.lower()

    # Extract all amounts - be more specific to avoid matching dates
    amount_patterns = [
        r'for\s+(\d+(?:\.\d{2})?)\s*(?:rs|inr|usd|\$|dollars?|bucks?|rupees?)',  # for 123 rs
        r'at\s+(\d+(?:\.\d{2})?)\s*(?:rs|inr|usd|\$|dollars?|bucks?|rupees?)',  # at 123 rs
        r'(\d+(?:\.\d{2})?)\s*(?:rs|inr|usd|\$|dollars?|bucks?|rupees?)(?:\s|$)',  # 123 rs (more flexible)
        r'\$\s*(\d+(?:\.\d{2})?)',  # $123
        r'(\d+(?:\.\d{2})?)\s*dollars?',  # 123 dollars
        r'(\d+(?:\.\d{2})?)\s*bucks?',  # 123 bucks
        r'(\d+(?:\.\d{2})?)\s*rupees?',  # 123 rupees
        r'(\d+(?:\.\d{2})?)\s*₹',  # 123 ₹
    ]

    # Split the input into potential transaction parts
    transaction_parts = re.split(r'\s+(?:and|&)\s+|,\s*', user_input.strip(), flags=re.IGNORECASE)

    # Create transactions for each part that has an amount
    transactions = []
    for part in transaction_parts:
        part = part.strip()
        if not part:
            continue

        # Try LLM-based extraction first (primary method for agentic AI)
        transaction = None
        try:
            from ..agents.components.nl_processor import NaturalLanguageProcessor
            nl_processor = NaturalLanguageProcessor()
            llm_extraction = nl_processor.process_input(part)

            if llm_extraction and llm_extraction.get('confidence', 0) >= 0.7:
                # Use LLM extraction results
                transaction = {
                    "amount": None,  # Will be processed below
                    "description": llm_extraction.get('description') or part.strip(),
                    "date": llm_extraction.get('date'),
                    "merchant": llm_extraction.get('merchant'),
                    "category": llm_extraction.get('category')
                }

                # Validate and post-process the date from LLM extraction
                llm_date = llm_extraction.get('date')
                if llm_date:
                    # Check if date is in proper YYYY-MM-DD format
                    import re
                    if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(llm_date)):
                        # Invalid or incomplete date format, set to None for regex fallback
                        logger.warning(f"LLM returned invalid date format '{llm_date}' for '{part}', falling back to regex date parsing")
                        transaction["date"] = None
                    else:
                        # Valid date format, keep it
                        transaction["date"] = llm_date

                # Process amount from LLM extraction
                if llm_extraction.get('amount'):
                    # Extract numeric amount from LLM result
                    import re
                    amount_match = re.search(r'(\d+(?:\.\d{2})?)', str(llm_extraction.get('amount')))
                    if amount_match:
                        amount = float(amount_match.group(1))
                        # Determine if income or expense based on keywords in original text
                        part_lower = part.lower()

                        # Separate keyword lists for better classification
                        income_keywords = [
                            "earned", "received", "income", "credit", "deposit", "salary", "wage", "payroll",
                            "refund", "reimbursement", "bonus", "commission", "tips", "tip", "freelance", "payment received",
                            "paid me", "got paid", "made", "collected", "withdrawal", "transfer in", "cashback",
                            "interest", "dividend", "royalty", "prize", "award", "grant", "stipend", "allowance",
                            "pension", "social security", "unemployment", "gift", "inheritance", "lottery",
                            "settlement", "compensation", "profit", "revenue", "sales", "consulting", "contract",
                            "rental income", "lease income"  # More specific for income context
                        ]

                        expense_keywords = [
                            "spent", "paid", "bought", "purchased", "cost", "fee", "bill", "rent payment",
                            "mortgage", "insurance", "utility", "gas", "electricity", "water", "internet",
                            "phone", "subscription", "membership", "donation", "taxes", "fine", "penalty"
                        ]

                        # Check for explicit expense keywords first
                        has_expense_keywords = any(word in part_lower for word in expense_keywords)
                        has_income_keywords = any(word in part_lower for word in income_keywords)

                        # Special handling for ambiguous words
                        # "got paid" should always be income, not expense
                        if "got paid" in part_lower:
                            has_expense_keywords = False
                            has_income_keywords = True

                        # If explicit expense keywords found, it's an expense
                        if has_expense_keywords:
                            amount = -amount  # Definitely expense
                        # If income keywords found but no expense keywords, it's income
                        elif has_income_keywords:
                            pass  # Keep as positive (income)
                        # Default to expense if ambiguous
                        else:
                            amount = -amount  # Default to expense
                        transaction["amount"] = amount
                        logger.info(f"LLM extracted amount: {amount} for '{part}' (confidence: {llm_extraction.get('confidence', 0)})")

                if transaction["amount"] is not None:
                    transactions.append(transaction)
                    continue  # Successfully used LLM extraction
                else:
                    logger.warning(f"LLM extraction incomplete for '{part}', falling back to regex")
            else:
                logger.info(f"LLM extraction low confidence ({llm_extraction.get('confidence', 0) if llm_extraction else 0}), falling back to regex")

        except Exception as e:
            logger.warning(f"LLM extraction failed for '{part}': {e}, falling back to regex")

        # Fallback to regex + keyword logic (current implementation)
        part_lower = part.lower()
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, part_lower)
            if match:
                amount = float(match.group(1))
                # Check for income keywords - expanded comprehensive list
                income_keywords = [
                    "earned", "received", "income", "credit", "deposit", "salary", "wage", "payroll",
                    "refund", "reimbursement", "bonus", "commission", "tips", "tip", "freelance", "payment received",
                    "paid me", "got paid", "made", "collected", "withdrawal", "transfer in", "cashback",
                    "interest", "dividend", "royalty", "prize", "award", "grant", "stipend", "allowance",
                    "pension", "social security", "unemployment", "gift", "inheritance", "lottery",
                    "settlement", "compensation", "profit", "revenue", "sales", "consulting", "contract",
                    "rental income", "lease income"  # More specific for income context
                ]

                expense_keywords = [
                    "spent", "paid", "bought", "purchased", "cost", "fee", "bill", "rent payment",
                    "mortgage", "insurance", "utility", "gas", "electricity", "water", "internet",
                    "phone", "subscription", "membership", "donation", "taxes", "fine", "penalty"
                ]

                # Check for explicit expense keywords first
                has_expense_keywords = any(word in part_lower for word in expense_keywords)
                has_income_keywords = any(word in part_lower for word in income_keywords)

                # Special handling for ambiguous words
                # "got paid" should always be income, not expense
                if "got paid" in part_lower:
                    has_expense_keywords = False
                    has_income_keywords = True

                # If explicit expense keywords found, it's an expense
                if has_expense_keywords:
                    amount = -amount  # Definitely expense
                # If income keywords found but no expense keywords, it's income
                elif has_income_keywords:
                    pass  # Keep as positive (income)
                # Default to expense if ambiguous
                else:
                    amount = -amount  # Default to expense
                break

        if amount is None:
            continue  # Skip parts without amounts

        # Initialize transaction dictionary for regex fallback
        transaction = {
            "amount": amount,
            "description": part.strip(),
            "date": None,  # Will be set below
            "merchant": None,  # Will be set below
            "category": None  # Will be set below
        }

        # Extract date from this part
        today = datetime.now().date()
        if any(word in part_lower for word in ["today", "this morning", "this afternoon", "this evening", "this month"]):
            transaction["date"] = today.isoformat()
        elif any(word in part_lower for word in ["yesterday"]):
            transaction["date"] = (today - timedelta(days=1)).isoformat()
        elif "last" in part_lower and "week" in part_lower:
            transaction["date"] = (today - timedelta(days=7)).isoformat()
        else:
            # Look for date patterns in this part
            date_patterns = [
                r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)',  # 9th september
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
                r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD
            ]
            for pattern in date_patterns:
                match = re.search(pattern, part, re.IGNORECASE)
                if match:
                    try:
                        if r'(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)' in pattern:
                            # Day month format like "9th september"
                            day, month_name = match.groups()
                            day = int(day)
                            month_names = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }
                            month = month_names.get(month_name.lower())
                            if month:
                                year = datetime.now().year  # Assume current year
                                parsed_date = datetime(year, month, day).date()
                                transaction["date"] = parsed_date.isoformat()
                                break
                        elif pattern.startswith(r'(\d{4})'):  # YYYY/MM/DD
                            year, month, day = map(int, match.groups())
                            parsed_date = datetime(year, month, day).date()
                            transaction["date"] = parsed_date.isoformat()
                            break
                        else:  # Assume MM/DD/YYYY
                            month, day, year = map(int, match.groups())
                            parsed_date = datetime(year, month, day).date()
                            transaction["date"] = parsed_date.isoformat()
                            break
                    except ValueError:
                        continue

        # Set default date to today if no date was found
        if transaction.get("date") is None:
            transaction["date"] = today.isoformat()

        # Extract merchant from the original part (before cleaning)
        merchant = None

        # First try regex extraction for explicit patterns
        from_match = re.search(r'\bfrom\s+([a-zA-Z\s]+?)(?:\s+(?:for|at|on)|\s*$)', part, re.IGNORECASE)
        if from_match:
            merchant_name = from_match.group(1).strip()
            if len(merchant_name) > 2:
                merchant = merchant_name.title()
        else:
            at_match = re.search(r'\bat\s+([a-zA-Z\s]+?)(?:\s+for|\s*$)', part, re.IGNORECASE)
            if at_match:
                merchant_name = at_match.group(1).strip()
                if len(merchant_name) > 2:
                    merchant = merchant_name.title()

        # If regex didn't find anything, try NER agent
        if not merchant:
            try:
                from ..agents.ner_merchant_agent import NERMerchantAgent
                ner_agent = NERMerchantAgent()
                extracted_merchant, confidence = ner_agent.extract_merchant_name(part)
                if extracted_merchant and confidence >= 0.7:  # Higher threshold for NER
                    merchant = extracted_merchant
            except Exception as e:
                logger.warning(f"NER merchant extraction failed: {e}")

        # Extract description from this part - create a meaningful summary
        description = part.strip()

        # Remove amounts and currencies
        description = re.sub(r'\b\d+(?:\.\d{2})?\s*(?:rs|inr|usd|\$|dollars?|bucks?|rupees?)\b', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\$\s*\d+(?:\.\d{2})?', '', description)
        description = re.sub(r'\b\d+(?:\.\d{2})?\s*dollars?', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\b\d+(?:\.\d{2})?\s*bucks?', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\b\d+(?:\.\d{2})?\s*rupees?', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\b\d+(?:\.\d{2})?\s*₹', '', description)

        # Remove dates
        description = re.sub(r'\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)', '', description, flags=re.IGNORECASE)

        # Remove merchant references
        description = re.sub(r'\bfrom\s+[a-zA-Z\s]+?(?:\s+(?:for|at|on)|\s*$)', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\bat\s+[a-zA-Z\s]+?(?:\s+for|\s*$)', '', description, flags=re.IGNORECASE)

        # Remove some filler words but keep product names - be more selective
        filler_words = [
            'i', 'we', 'you', 'they', 'he', 'she', 'it', 'spent', 'bought', 'purchased', 'paid', 'gave',
            'received', 'earned', 'got', 'had', 'made', 'did', 'went', 'ate', 'drank', 'used', 'bought',
            'paid for', 'for', 'at', 'to', 'with', 'by', 'on', 'in', 'the', 'a', 'an', 'and', 'or', 'but',
            'so', 'because', 'although', 'while', 'when', 'where', 'how', 'why', 'what', 'which', 'who',
            'whose', 'that', 'this', 'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'mine', 'yours', 'hers', 'ours', 'theirs', 'also', 'myself', 'yourself', 'himself', 'herself',
            'itself', 'ourselves', 'yourselves', 'themselves', 'today', 'yesterday', 'tomorrow', 'last',
            'next', 'week', 'month', 'year', 'dollars', 'bucks', 'rupees', 'rs'
        ]
        # Only remove filler words that are standalone (word boundaries)
        for word in filler_words:
            description = re.sub(rf'\b{re.escape(word)}\b', '', description, flags=re.IGNORECASE)

        # Clean up extra spaces
        description = ' '.join(description.split())

        # If description is too short or empty, create a meaningful default
        if not description.strip() or len(description.strip()) < 3:
            if merchant:
                description = f"Purchase at {merchant}"
            else:
                description = "Purchase"

        # Infer merchant from description if not already found
        if not transaction.get("merchant"):
            description_lower = transaction["description"].lower()
            merchants = {
                "starbucks": "Starbucks",
                "mcdonalds": "McDonald's",
                "mcdonald's": "McDonald's",
                "walmart": "Walmart",
                "target": "Target",
                "amazon": "Amazon",
                "uber": "Uber",
                "lyft": "Lyft",
                "netflix": "Netflix",
                "spotify": "Spotify",
                "coffee bean": "Coffee Bean",
                "coffeebean": "Coffee Bean"
            }
            for key, merchant_name in merchants.items():
                if key in description_lower:
                    transaction["merchant"] = merchant_name
                    break

        # Infer category using simple keyword-based classification
        if transaction.get("description") and not transaction.get("category"):
            try:
                # Check if this is an income transaction (positive amount)
                is_income = transaction.get("amount", 0) > 0
                description_lower = transaction["description"].lower()

                if is_income:
                    # Income categories
                    income_categories = {
                        "salary": ["salary", "wage", "payroll", "paycheck", "compensation"],
                        "rental income": ["rent", "rental", "lease", "tenant", "property income"],
                        "freelance": ["freelance", "consulting", "contract", "gig", "side hustle"],
                        "investment": ["dividend", "interest", "capital gain", "stock", "bond", "investment"],
                        "business": ["business", "revenue", "sales", "profit", "commission"],
                        "gift": ["gift", "inheritance", "lottery", "prize", "award", "grant"],
                        "refund": ["refund", "reimbursement", "tax refund", "cashback"],
                        "other income": ["other", "miscellaneous", "additional", "bonus", "tip"]
                    }
                    for category, keywords in income_categories.items():
                        if any(keyword in description_lower for keyword in keywords):
                            transaction["category"] = category.title()
                            break
                else:
                    # Expense categories
                    expense_categories = {
                        "food": ["restaurant", "cafe", "coffee", "lunch", "dinner", "eat", "food", "milkshake", "barista"],
                        "shopping": ["clothes", "dress", "shirt", "shoes", "store", "shopping", "jumpsuit"],
                        "transportation": ["uber", "lyft", "taxi", "bus", "train", "gas", "fuel"],
                        "entertainment": ["netflix", "spotify", "movie", "game", "concert"],
                        "utilities": ["electric", "water", "internet", "phone", "gas bill"]
                    }
                    for category, keywords in expense_categories.items():
                        if any(keyword in description_lower for keyword in keywords):
                            transaction["category"] = category.title()
                            break

                # If still no category, try merchant-based inference
                if not transaction.get("category") and transaction.get("merchant"):
                    merchant_lower = transaction["merchant"].lower()
                    if is_income:
                        # For income transactions, merchant might represent the source
                        if any(word in merchant_lower for word in ["employer", "company", "client", "customer"]):
                            transaction["category"] = "Salary"
                        elif any(word in merchant_lower for word in ["bank", "investment", "brokerage"]):
                            transaction["category"] = "Investment"
                        elif any(word in merchant_lower for word in ["tenant", "renter"]):
                            transaction["category"] = "Rental Income"
                        else:
                            transaction["category"] = "Other Income"
                    else:
                        # Expense merchant inference
                        if "barista" in merchant_lower or "coffee" in merchant_lower:
                            transaction["category"] = "Food"
                        elif "uber" in merchant_lower or "lyft" in merchant_lower:
                            transaction["category"] = "Transportation"

            except Exception as e:
                logger.warning(f"Category classification failed: {e}")

        transactions.append(transaction)

    # Auto-assign today's date for transactions without explicit dates
    today = datetime.now().date().isoformat()
    for tx in transactions:
        if not tx.get("date"):
            tx["date"] = today
            logger.info(f"Auto-assigned today's date ({today}) to transaction: {tx.get('description', 'Unknown')}")

    return transactions


async def _generate_conversational_response(
    transaction: Dict[str, Any],
    missing_fields: List[str],
    conversation_context: Dict[str, Any]
) -> str:
    """
    Generate a conversational response asking for missing information
    """
    responses = {
        "amount": "How much did you spend? Please include the dollar amount.",
        "description": "What did you purchase or what was this transaction for?",
        "date": "When did this transaction occur? Please provide the date."
    }

    if len(missing_fields) == 1:
        field = missing_fields[0]
        return f"I need a bit more information. {responses[field]}"
    else:
        fields_text = ", ".join(missing_fields[:-1]) + f" and {missing_fields[-1]}"
        return f"I need some more details. Could you please provide the {fields_text}?"

    # Show what we already understood
    understood = []
    if transaction.get("amount"):
        understood.append(f"💰 Amount: ${abs(transaction['amount']):.2f}")
    if transaction.get("description"):
        understood.append(f"📝 Description: {transaction['description']}")
    if transaction.get("date"):
        understood.append(f"📅 Date: {transaction['date']}")

    if understood:
        response += "\n\nI already understood:\n" + "\n".join(understood)

    return response
