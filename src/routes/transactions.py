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

from ..models.transaction import Transaction, TransactionCreate, TransactionUpdate, TransactionResponse
from ..models.user import User
from ..services.transaction_service import TransactionService
from ..services.auth_service import get_current_user
from ..core.database import get_db_session

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/upload", response_model=Dict[str, Any])
async def upload_transactions(
    file: UploadFile = File(...),
    file_type: str = "csv",
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
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
        transaction_service = TransactionService(db)
        
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
            "new_transactions": result["new"],
            "duplicates_found": result["duplicates"],
            "errors": result.get("errors", [])
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
    db = Depends(get_db_session)
):
    """
    Get transactions with filtering and pagination
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Create a new transaction
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Get a specific transaction
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Update a transaction
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Delete a transaction
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Create multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Update multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Delete multiple transactions in batch
    """
    try:
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
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
        
        transaction_service = TransactionService(db)
        
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
    db = Depends(get_db_session)
):
    """
    Get transaction summary statistics
    """
    try:
        transaction_service = TransactionService(db)
        
        summary = await transaction_service.get_transaction_summary(
            user.id, start_date, end_date
        )
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
