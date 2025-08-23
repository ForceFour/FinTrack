"""
Agent Models - Data models for multi-agent system management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    """Types of agents in the system"""
    CATEGORIZATION = "categorization"
    FRAUD_DETECTION = "fraud_detection"
    ANALYTICS = "analytics"
    SUGGESTIONS = "suggestions"
    SECURITY_MONITOR = "security_monitor"
    ORCHESTRATOR = "orchestrator"

class AgentState(str, Enum):
    """Agent operational states"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class AgentStatus(BaseModel):
    """Agent status information"""
    agent_id: str
    agent_type: AgentType
    state: AgentState
    current_task: Optional[str] = None
    tasks_in_queue: int = 0
    last_activity: datetime
    uptime: int  # seconds
    performance_metrics: Dict[str, Union[int, float]]
    health_status: str = "healthy"  # "healthy", "degraded", "unhealthy"
    error_count: int = 0
    last_error: Optional[str] = None

class AgentTask(BaseModel):
    """Agent task definition"""
    task_id: str
    agent_type: AgentType
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class AgentResponse(BaseModel):
    """Agent task response"""
    task_id: str
    agent_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    execution_time: float  # seconds
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}
    error_details: Optional[Dict[str, Any]] = None

class WorkflowRequest(BaseModel):
    """Multi-agent workflow request"""
    workflow_id: Optional[str] = None
    workflow_type: str
    input_data: Dict[str, Any]
    agent_sequence: List[AgentType]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[int] = None  # seconds
    callback_url: Optional[str] = None

class WorkflowStatus(BaseModel):
    """Workflow execution status"""
    workflow_id: str
    workflow_type: str
    status: TaskStatus
    current_agent: Optional[AgentType] = None
    completed_agents: List[AgentType]
    progress: float = 0.0
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    agent_results: Dict[str, AgentResponse] = {}

class AgentCommunication(BaseModel):
    """Inter-agent communication message"""
    message_id: str
    sender_agent: AgentType
    receiver_agent: AgentType
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: TaskPriority = TaskPriority.NORMAL
    requires_response: bool = False
    correlation_id: Optional[str] = None

class AgentMetrics(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    agent_type: AgentType
    tasks_completed: int
    tasks_failed: int
    average_execution_time: float
    success_rate: float
    throughput: float  # tasks per minute
    resource_usage: Dict[str, float]
    uptime_percentage: float
    last_reset: datetime

class WorkflowDefinition(BaseModel):
    """Workflow definition"""
    workflow_type: str
    name: str
    description: str
    agents: List[AgentType]
    execution_order: str  # "sequential", "parallel", "conditional"
    conditions: Optional[Dict[str, Any]] = {}
    timeout: int = 300  # seconds
    retry_policy: Dict[str, Any] = {}

class AgentConfiguration(BaseModel):
    """Agent configuration settings"""
    agent_type: AgentType
    config: Dict[str, Any]
    llm_settings: Optional[Dict[str, Any]] = {}
    performance_thresholds: Dict[str, float]
    resource_limits: Dict[str, Union[int, float]]
    enabled: bool = True

class SystemStatus(BaseModel):
    """Overall system status"""
    system_health: str  # "healthy", "degraded", "critical"
    active_agents: int
    total_agents: int
    active_workflows: int
    total_tasks_today: int
    system_load: float
    last_updated: datetime
    alerts: List[Dict[str, Any]]
