"""
Backend API Routes - Multi-Agent System Management
Handles agent orchestration, communication, and workflow management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio

from ..models.user import User
from ..models.agent import (
    AgentStatus, AgentTask, AgentResponse,
    WorkflowRequest, WorkflowStatus
)
from ..services.mock_services import AgentOrchestrator, ConnectionManager
from ..core.database_config import get_db_client

router = APIRouter(prefix="/agents", tags=["agents"])
manager = ConnectionManager()

@router.get("/status", response_model=Dict[str, Any])
async def get_agents_status(
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Get status of all agents in the system
    """
    try:
        orchestrator = AgentOrchestrator(db)

        status = await orchestrator.get_all_agents_status(user_id)

        return {
            "agents": status,
            "total_agents": len(status),
            "active_agents": len([a for a in status if a["status"] == "active"]),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{agent_type}", response_model=AgentStatus)
async def get_agent_status(
    agent_type: str,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Get status of a specific agent
    """
    try:
        orchestrator = AgentOrchestrator(db)

        # Validate agent type
        valid_agents = [
            "categorization", "fraud_detection", "analytics",
            "suggestions", "security_monitor", "orchestrator"
        ]

        if agent_type not in valid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type. Valid types: {valid_agents}"
            )

        status = await orchestrator.get_agent_status(agent_type, user_id)

        return status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task", response_model=Dict[str, Any])
async def submit_agent_task(
    task_request: AgentTask,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Submit a task to a specific agent
    """
    try:
        orchestrator = AgentOrchestrator(db)

        # Add user context to task
        task_data = task_request.dict()
        task_data["user_id"] = user_id
        task_data["submitted_at"] = datetime.now()

        task_id = await orchestrator.submit_task(task_data)

        return {
            "status": "success",
            "task_id": task_id,
            "message": f"Task submitted to {task_request.agent_type} agent",
            "estimated_completion": "2-5 minutes"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}", response_model=Dict[str, Any])
async def get_task_status(
    task_id: str,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Get status of a specific task
    """
    try:
        orchestrator = AgentOrchestrator(db)

        task_status = await orchestrator.get_task_status(task_id, user_id)

        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")

        return task_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow", response_model=Dict[str, Any])
async def start_workflow(
    workflow_request: WorkflowRequest,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Start a multi-agent workflow
    """
    try:
        orchestrator = AgentOrchestrator(db)

        # Add user context
        workflow_data = workflow_request.dict()
        workflow_data["user_id"] = user_id
        workflow_data["started_at"] = datetime.now()

        workflow_id = await orchestrator.start_workflow(workflow_data)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "message": f"Started {workflow_request.workflow_type} workflow",
            "agents_involved": workflow_request.agent_sequence,
            "estimated_duration": "5-15 minutes"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(
    workflow_id: str,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Get status of a workflow
    """
    try:
        orchestrator = AgentOrchestrator(db)

        workflow_status = await orchestrator.get_workflow_status(workflow_id, user_id)

        if not workflow_status:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return workflow_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categorization/batch", response_model=Dict[str, Any])
async def batch_categorize_transactions(
    transactions: List[Dict[str, Any]],
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Submit batch categorization task to categorization agent
    """
    try:
        orchestrator = AgentOrchestrator(db)

        task_data = {
            "agent_type": "categorization",
            "action": "batch_categorize",
            "data": {
                "transactions": transactions,
                "user_id": user_id
            },
            "priority": "normal"
        }

        task_id = await orchestrator.submit_task(task_data)

        return {
            "status": "success",
            "task_id": task_id,
            "transactions_count": len(transactions),
            "message": "Batch categorization started"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fraud-detection/scan", response_model=Dict[str, Any])
async def run_fraud_detection(
    scan_data: Dict[str, Any],
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Run fraud detection analysis
    """
    try:
        orchestrator = AgentOrchestrator(db)

        task_data = {
            "agent_type": "fraud_detection",
            "action": "analyze_transactions",
            "data": {
                **scan_data,
                "user_id": user_id
            },
            "priority": "high"
        }

        task_id = await orchestrator.submit_task(task_data)

        return {
            "status": "success",
            "task_id": task_id,
            "message": "Fraud detection analysis started",
            "scan_scope": scan_data.get("scope", "recent_transactions")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/generate", response_model=Dict[str, Any])
async def generate_analytics(
    analytics_request: Dict[str, Any],
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Generate analytics reports using analytics agent
    """
    try:
        orchestrator = AgentOrchestrator(db)

        task_data = {
            "agent_type": "analytics",
            "action": "generate_report",
            "data": {
                **analytics_request,
                "user_id": user_id
            },
            "priority": "normal"
        }

        task_id = await orchestrator.submit_task(task_data)

        return {
            "status": "success",
            "task_id": task_id,
            "message": "Analytics generation started",
            "report_type": analytics_request.get("report_type", "comprehensive")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggestions/personalized", response_model=Dict[str, Any])
async def generate_personalized_suggestions(
    suggestion_request: Dict[str, Any],
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Generate personalized suggestions using AI agent
    """
    try:
        orchestrator = AgentOrchestrator(db)

        task_data = {
            "agent_type": "suggestions",
            "action": "generate_personalized",
            "data": {
                **suggestion_request,
                "user_id": user_id
            },
            "priority": "normal"
        }

        task_id = await orchestrator.submit_task(task_data)

        return {
            "status": "success",
            "task_id": task_id,
            "message": "Personalized suggestions generation started",
            "suggestion_types": suggestion_request.get("types", ["all"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", response_model=Dict[str, Any])
async def get_agent_logs(
    agent_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    start_date: Optional[datetime] = Query(default=None),
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Get agent activity logs
    """
    try:
        orchestrator = AgentOrchestrator(db)

        logs = await orchestrator.get_agent_logs(
            user_id=user_id,
            agent_type=agent_type,
            limit=limit,
            start_date=start_date
        )

        return {
            "logs": logs,
            "count": len(logs),
            "filter_agent": agent_type,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_type}/restart", response_model=Dict[str, Any])
async def restart_agent(
    agent_type: str,
        user_id: str = Query(...),
        db = Depends(get_db_client)
):
    """
    Restart a specific agent (admin function)
    """
    try:
        # TODO: Implement admin check in frontend with Supabase roles
        # For now, all authenticated users can restart agents

        orchestrator = AgentOrchestrator(db)

        success = await orchestrator.restart_agent(agent_type)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart {agent_type} agent"
            )

        return {
            "status": "success",
            "message": f"{agent_type} agent restarted successfully",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time agent status updates
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))

            elif message.get("type") == "subscribe_agent":
                agent_type = message.get("agent_type")
                # Subscribe to specific agent updates
                await manager.subscribe_to_agent(user_id, agent_type)

            # Echo received message for debugging
            await websocket.send_text(json.dumps({
                "type": "echo",
                "data": message
            }))

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconnected from WebSocket")

# Function to broadcast agent status updates (called by orchestrator)
async def broadcast_agent_update(user_id: str, agent_type: str, status_data: Dict[str, Any]):
    """
    Broadcast agent status update to connected clients
    """
    message = {
        "type": "agent_update",
        "agent_type": agent_type,
        "status": status_data,
        "timestamp": datetime.now().isoformat()
    }

    await manager.send_personal_message(json.dumps(message), user_id)

async def broadcast_workflow_update(user_id: str, workflow_id: str, status_data: Dict[str, Any]):
    """
    Broadcast workflow status update to connected clients
    """
    message = {
        "type": "workflow_update",
        "workflow_id": workflow_id,
        "status": status_data,
        "timestamp": datetime.now().isoformat()
    }

    await manager.send_personal_message(json.dumps(message), user_id)
