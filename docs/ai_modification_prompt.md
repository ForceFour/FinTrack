# AI Prompt for Modifying Existing Project to Agentic Expense Tracker

## Context
I need to transform an existing project into a multi-agent AI-based expense tracking system for my university assignment. The system must integrate LLMs, NLP, Information Retrieval, Security features, and Agent Communication Protocols using LangGraph and LangChain frameworks. 

**Package Manager**: UV (modern Python package manager)
**Frontend**: Streamlit for interactive web interface
**Backend**: FastAPI for REST APIs

## System Requirements

### **Multi-Agent Architecture (6 Agents)**
1. **Ingestion Agent**: Normalize raw transaction data
2. **NER/Merchant Agent**: Extract and standardize merchant information
3. **Classifier Agent**: Predict expense categories using ML/LLM
4. **Pattern Analyzer Agent**: Detect spending patterns and recurring habits
5. **Suggestion Agent**: Generate actionable financial recommendations
6. **Safety & Compliance Guard Agent**: Flag anomalies and ensure security

### **Technical Stack**
- **Package Manager**: UV for dependency management and virtual environments
- **Framework**: LangGraph + LangChain for multi-agent workflows
- **API**: FastAPI for REST endpoints
- **Frontend**: Streamlit for interactive dashboard and user interface
- **LLM**: Integration with OpenAI/Anthropic/local models
- **NLP**: Named Entity Recognition, Text Classification, Summarization
- **IR**: Merchant database search, pattern matching
- **Security**: JWT auth, input sanitization, data encryption
- **Database**: PostgreSQL/SQLite for transaction storage

### **Data Flow**
```
Raw Transactions → Ingestion → NER/Merchant → Classifier → Pattern Analyzer → Suggestion → Safety Guard → Output
```

## Modification Instructions

### **1. Core Structure Setup**
Please create/modify the existing project to include:

```python
# Main workflow using LangGraph
from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage

class TransactionState(TypedDict):
    raw_data: Dict
    processed_data: Dict
    merchant_info: Dict
    category: str
    patterns: List[Dict]
    suggestions: List[str]
    safety_flags: List[str]
    user_id: str

# State graph workflow
workflow = StateGraph(TransactionState)
```

### **2. Agent Implementation Pattern**
Each agent should follow this pattern:

```python
class BaseAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
    
    async def execute(self, state: TransactionState) -> TransactionState:
        # Agent-specific logic
        pass
    
    def communicate(self, message, target_agent):
        # Inter-agent communication
        pass
```

### **3. Streamlit Frontend Integration**
Create interactive Streamlit pages:

```python
# streamlit_app.py
import streamlit as st
from src.services.api_client import ExpenseTrackerAPI

st.set_page_config(
    page_title="Agentic Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🤖 Agentic Expense Tracker")
    st.sidebar.title("Navigation")
    
    # Initialize API client
    api_client = ExpenseTrackerAPI()
    
    # File upload section
    uploaded_file = st.file_uploader(
        "Upload Transaction File", 
        type=['csv', 'json'],
        help="Upload your bank statement or transaction export"
    )
    
    if uploaded_file:
        # Trigger agent workflow through API
        with st.spinner("Processing through AI agents..."):
            results = api_client.process_transactions(uploaded_file)
        
        # Display results
        st.success("✅ Processing Complete!")
        display_results(results)

# pages/01_📊_Dashboard.py
import streamlit as st
import plotly.express as px

st.title("📊 Expense Dashboard")

# Real-time agent status
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Transactions Processed", "1,234", "12%")
with col2:
    st.metric("Categories Identified", "23", "3%")
with col3:
    st.metric("Suggestions Generated", "8", "2%")

# Agent workflow visualization
st.subheader("🤖 Agent Workflow Status")
agent_status = st.empty()  # Real-time updates
```

### **4. FastAPI Backend Integration**
Create REST endpoints for Streamlit to consume:

```python
@app.post("/api/transactions/upload")
async def upload_transactions(file: UploadFile):
    # Trigger agent workflow
    pass

@app.get("/api/transactions/{user_id}/analyze")
async def analyze_spending(user_id: str):
    # Return analysis results for Streamlit charts
    pass

@app.get("/api/suggestions/{user_id}")
async def get_suggestions(user_id: str):
    # Return personalized suggestions for Streamlit display
    pass

@app.websocket("/api/ws/agent-status")
async def websocket_agent_status(websocket: WebSocket):
    # Real-time agent status for Streamlit
    pass
```
Include:
- Bias detection in category classification
- Explainable AI for suggestions
- Privacy protection for financial data
- User consent management
- Audit logging

### **5. Responsible AI Implementation**
Implement:
- JWT-based authentication
- Input validation and sanitization
- Data encryption at rest and in transit
- Rate limiting
- Anomaly detection

### **6. Security Features**

## Specific Requirements

### **UV Package Management Setup**
The project must use UV package manager:

```toml
# pyproject.toml
[project]
name = "agentic-expense-tracker"
version = "0.1.0"
description = "Multi-agent AI expense tracking system"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "streamlit>=1.28.0",
    "langgraph>=0.2.0",
    "langchain>=0.2.0",
    "langchain-openai>=0.1.0",
    "uvicorn>=0.24.0",
    "pandas>=2.1.0",
    "numpy>=1.24.0",
    "scikit-learn>=1.3.0",
    "plotly>=5.17.0",
    "pydantic>=2.5.0",
    "python-multipart>=0.0.6",
    "python-jose>=3.3.0",
    "passlib>=1.7.4",
    "bcrypt>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.9.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
]
```

Setup commands:
```bash
# Initialize UV project
uv init
uv add fastapi streamlit langgraph langchain
uv add --dev pytest black ruff mypy

# Run development servers
uv run uvicorn src.api.main:app --reload --port 8000
uv run streamlit run frontend/streamlit_app.py --server.port 8501
```
### **File Structure Modifications**
- Convert existing structure to match the provided folder structure with UV package management
- Create interactive Streamlit pages for each major functionality
- Ensure seamless FastAPI-Streamlit integration
- Ensure modular agent design with clear separation of concerns
- Include comprehensive testing framework

- Add configuration management for different environments

### **Streamlit-Specific Features**

1. **Interactive Dashboard**
   - Real-time agent workflow visualization
   - Interactive charts with Plotly
   - File upload with drag-and-drop
   - Progress bars for agent processing

2. **Multi-page Application**
   - Dashboard: Overview and metrics
   - Upload: Transaction file processing
   - Category Management: Manual category assignment
   - Analytics: Deep spending analysis
   - Suggestions: AI-generated recommendations
   - Security Monitor: Anomaly detection results

3. **State Management**
   - Session state for user data
   - Real-time API communication
   - Caching for performance optimization

### **Key Features to Implement**
1. **Transaction Processing Pipeline**
   - Streamlit file uploader for CSV/JSON files
   - Real-time progress visualization during agent processing
   - Data validation and error handling with user feedback

2. **Intelligence Layer**
2. **Intelligence Layer**
   - LLM-powered merchant recognition with confidence scores
   - ML-based category classification with explainable results
   - Pattern detection with interactive visualizations
   - Natural language suggestion generation in chat-like interface

3. **Information Retrieval**
3. **Information Retrieval**
   - Searchable merchant database within Streamlit
   - Historical transaction search with filters
   - Interactive spending pattern templates
   - Budget recommendation engine with sliders and inputs

4. **Communication Protocols**
4. **Communication Protocols**
   - FastAPI backend serving Streamlit frontend
   - WebSocket for real-time agent status updates
   - Message queuing between agents with live monitoring
   - Event-driven architecture with notification system

## Expected Output

Please provide:

Please provide:

1. **Complete file structure** with UV package management setup
2. **Core agent implementations** with placeholder logic
3. **FastAPI application** with Streamlit-compatible endpoints
4. **Streamlit multi-page application** with interactive components
5. **LangGraph workflow** connecting all agents
6. **pyproject.toml** with UV dependencies
7. **Basic test structure** for unit and integration testing
8. **README.md** with UV setup and running instructions
9. **Development scripts** for running both FastAPI and Streamlit servers

## Additional Considerations

- **Performance**: Ensure agents can process transactions efficiently
- **Scalability**: Design for multiple concurrent users
- **Maintainability**: Use clean code principles and documentation
- **Deployment**: Include Docker and UV-compatible deployment scripts
- **Monitoring**: Add logging and basic metrics collection accessible via Streamlit
- **User Experience**: Ensure seamless interaction between Streamlit frontend and FastAPI backend

## Sample Transaction Data Format
```json
{
    "date": "2024-01-15",
    "amount": -45.67,
    "description": "STARBUCKS STORE #12345 NEW YORK NY",
    "payment_method": "Credit Card",
    "account_type": "Checking"
}
```

Transform the existing project structure to implement this agentic expense tracking system with all the specified components, ensuring it meets university assignment requirements for LLM integration, NLP, IR, security, and responsible AI practices.

**Key Integration Points:**
- Streamlit frontend communicates with FastAPI backend via HTTP requests
- Real-time agent status updates through WebSocket connections
- Interactive visualizations for agent workflow and results
- User-friendly file upload and data processing interface
- UV package manager for modern Python dependency management

**Development Workflow:**
```bash
# Setup
uv sync
uv run python scripts/setup_database.py

# Development
uv run python scripts/dev_server.py  # Runs both FastAPI and Streamlit

# Testing
uv run pytest

# Production
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
uv run streamlit run frontend/streamlit_app.py --server.port 8501
```