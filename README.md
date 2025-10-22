# Agentic Expense Tracker 🤖💰

**Multi-Agent AI-Powered Expense Tracking & Financial Analysis System**

A comprehensive university assignment project implementing multi-agent AI workflows using LangChain/LangGraph for intelligent financial management with Next.js frontend and FastAPI backend.

## 🎯 Project Overview

This system transforms traditional expense tracking into an intelligent, AI-driven financial analysis platform featuring:

- **6 Specialized AI Agents** working in coordinated workflows
- **Real-time Transaction Processing** with intelligent categorization  
- **Advanced Fraud Detection** and security monitoring
- **Personalized Financial Suggestions** powered by LLMs
- **Interactive Next.js Dashboard** with real-time updates
- **FastAPI Backend** with HTTP API for agent communication

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXT.JS FRONTEND                       │
│  📊 Dashboard | 📤 Upload | 🏷️ Categories | 📈 Analytics   │
│  💡 Suggestions | 🔒 Security Monitor | 🤖 Agent Status    │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
              │ FastAPI (AI Services)         │ Direct Queries
              │ HTTP API                      │ (CRUD Operations)
              │                               │
┌─────────────▼───────────────────┐  ┌────────▼──────────────┐
│      FASTAPI BACKEND            │  │  SUPABASE POSTGRESQL  │
│  🤖 LLM Services                │  │  💾 Transaction Store │
│  📤 File Upload/Processing      │  │  🔐 Row Level Security│
│  📊 Analytics Aggregation       │  │  ⚡ Real-time Queries │
│  🔄 Workflow Monitoring         │  │  🔍 Direct DB Access  │
└─────────────┬───────────────────┘  └───────────────────────┘
              │ LangGraph Workflows
┌─────────────▼───────────────────────────────────────────────┐
│                  MULTI-AGENT SYSTEM (LangGraph)            │
│  🏷️ NER Agent      │ � Merchant Agent │ � Classifier     │
│  💡 Suggestion Gen │ 🔒 Validator      │ 🎯 Orchestrator   │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 AI Agent System

### Agent Architecture
The system employs 6 specialized LangGraph agents for intelligent transaction processing:

1. **🏷️ NER (Named Entity Recognition) Agent**
   - Extracts merchant names, amounts, dates from transaction descriptions
   - **LLM-First Approach**: Uses OpenAI/Groq models as primary extraction method
   - **Fallback**: Regex patterns for standard formats when LLM fails
   - Handles natural language and unstructured text inputs

2. **🏪 Merchant Classification Agent**
   - Identifies and standardizes merchant names across transactions
   - **LLM-First Approach**: Context-aware merchant recognition and normalization
   - **Fallback**: String matching and fuzzy logic for known merchants
   - Learns merchant patterns from historical data

3. **📊 Transaction Classifier Agent**
   - Categorizes transactions into financial categories and subcategories
   - **LLM-First Approach**: Context-aware classification with reasoning
   - **Fallback**: scikit-learn ML models and rule-based classification
   - Provides confidence scores for each classification

4. **💡 Personalized Suggestion Agent**
   - Generates context-aware financial recommendations
   - Analyzes spending patterns and suggests optimizations
   - Creates actionable insights based on user behavior
   - Powered by LLM reasoning for personalized advice

5. **🔒 Validation Agent**
   - Ensures data quality and consistency across workflow
   - Validates extracted information and classifications
   - Flags anomalies and potential errors for review
   - Maintains data integrity throughout the pipeline

6. **🎯 Orchestrator Agent**
   - Coordinates workflow execution across all agents
   - Manages agent communication and state transitions
   - Handles error recovery and retry mechanisms
   - Optimizes agent execution order for efficiency

### LangGraph Integration
- **Workflow Definition**: Complex multi-step financial analysis workflows
- **Agent Communication**: Structured message passing between agents
- **State Management**: Persistent workflow state across agent interactions
- **Error Handling**: Robust error recovery and retry mechanisms

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- UV package manager
- OpenAI/Anthropic API keys (for LLM agents)

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd fintrack
uv sync  # Install all dependencies
```

2. **Environment Configuration**
```bash
# Create .env file
cp .env.example .env
# Add your API keys and configuration
```

3. **Start the Backend**
```bash
uv run python main.py
# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

4. **Start the Frontend**
```bash
cd fintrack-frontend
npm run dev
# Frontend will be available at http://localhost:3000
```

## 📱 Frontend Features

### Next.js React Application

#### 🏠 **Main Dashboard**
- Real-time agent status monitoring
- Financial summary cards and KPIs
- Interactive charts and visualizations
- Quick action buttons and navigation

#### 📤 **Transaction Upload**
- Drag-and-drop file upload (CSV, Excel, OFX)
- Real-time processing progress
- Duplicate detection and handling
- Batch categorization with AI

#### 🏷️ **Category Management**
- AI-powered categorization rules
- Custom category creation
- Rule-based automation setup
- Category performance analytics

#### 📈 **Advanced Analytics**
- Spending trends and patterns
- Budget vs. actual analysis
- Merchant and category breakdowns
- Forecasting and predictions

#### 💡 **AI Suggestions**
- Personalized financial recommendations
- Budget optimization advice
- Savings opportunity identification
- Goal achievement strategies

#### 🔒 **Security Monitor**
- Real-time fraud alerts
- Suspicious activity detection
- Security score dashboard
- Incident reporting and response

## 🔧 Backend Architecture

### Data Access Strategy

The application implements a **hybrid data access architecture** optimized for performance and intelligence:

#### 🗄️ Direct Supabase Queries (Transaction CRUD)
The frontend uses **direct PostgreSQL queries** via Supabase client for:
- **Transaction Management**: Create, Read, Update, Delete operations
- **Real-time Filtering**: Complex queries with multiple filter conditions
- **Pagination**: Efficient large dataset handling
- **Aggregations**: Client-side and database-level statistics
- **Security**: Row Level Security (RLS) policies enforce user data isolation

**Benefits:**
- Lower latency (no middleware layer)
- Database-level security enforcement
- Type-safe TypeScript integration
- Real-time subscription capabilities

#### 🤖 FastAPI Backend Services (AI & Workflows)

The backend handles **LLM-powered operations and orchestration** with 12 core endpoints:

**Analytics Services**
- `GET /api/v1/analytics/summary/dashboard?user_id={userId}` - Aggregated dashboard metrics

**Conversational AI**
- `POST /api/v1/transactions/natural-language` - Natural language transaction entry with LLM processing

**File Processing**
- `POST /api/v1/transactions/upload?user_id={userId}` - CSV/Excel upload triggering multi-agent pipeline

**Workflow Monitoring**
- `GET /api/v1/workflow/statistics/{userId}` - Workflow execution statistics
- `GET /api/v1/workflow/active/{userId}` - Active workflow tracking
- `GET /api/v1/workflow/history/{userId}` - Historical workflow logs
- `GET /api/v1/workflow/communications/{userId}` - Inter-agent communication logs

**User Management**
- `GET /api/v1/auth/me` - User profile retrieval
- `GET /api/v1/user-settings/{userId}` - User settings and preferences
- `PUT /api/v1/user-settings/{userId}` - Update user settings

**Transaction Intelligence**
- `POST /api/v1/categorize` - AI-powered single transaction categorization

**Health Monitoring**
- `GET /api/v1/health` - Service health check

### Why This Hybrid Architecture?

**Direct Supabase for CRUD:**
- ✅ Eliminates unnecessary API layer for simple operations
- ✅ Leverages PostgreSQL's query optimization
- ✅ Built-in RLS security at database level
- ✅ Reduces backend server load

**FastAPI for Intelligence:**
- ✅ Handles computationally intensive LLM operations
- ✅ Orchestrates multi-agent LangGraph workflows
- ✅ Manages complex file processing pipelines
- ✅ Provides centralized monitoring and logging

## 🏫 University Assignment Compliance

### Academic Requirements Met
- ✅ **Multi-Agent System**: 6 specialized AI agents with LangGraph orchestration
- ✅ **LLM Integration**: OpenAI/Anthropic APIs for natural language processing
- ✅ **Information Retrieval**: Advanced search and categorization capabilities
- ✅ **Security Features**: Fraud detection, anomaly detection, secure authentication
- ✅ **Agent Communication**: Structured protocols using LangGraph workflows
- ✅ **Responsible AI**: Ethical considerations, bias mitigation, transparency

### Technical Implementation
- **Framework**: LangChain + LangGraph for agent orchestration
- **Frontend**: Next.js 15 with React 19 and TypeScript
- **Backend**: FastAPI with async support (12 AI/workflow endpoints)
- **Database**: Supabase PostgreSQL with Row Level Security (RLS)
- **Data Access**: Hybrid architecture - Direct Supabase queries (CRUD) + FastAPI (AI operations)
- **Authentication**: Supabase Auth (built-in authentication service)
- **Security**: Row Level Security (RLS), input validation, rate limiting
- **Monitoring**: Comprehensive logging and error handling

## 🔬 Advanced Features

### AI & Machine Learning
- **Natural Language Processing**: Transaction description analysis
- **Anomaly Detection**: Statistical and ML-based fraud detection
- **Recommendation Engine**: Collaborative filtering for suggestions
- **Pattern Recognition**: Spending behavior analysis
- **Forecasting Models**: Time series prediction for budgeting

### Real-Time Capabilities
- **HTTP Polling**: Live agent status updates
- **Streaming Data**: Real-time transaction processing
- **Progressive Loading**: Chunked data loading for large datasets
- **Background Tasks**: Async processing for heavy operations

### Data Science Integration
- **Pandas Integration**: Advanced data manipulation and analysis
- **Plotly Visualizations**: Interactive charts and dashboards
- **Statistical Analysis**: Comprehensive financial metrics
- **Export Capabilities**: Multiple format support (CSV, Excel, JSON)

## 📊 Project Structure

```
fintrack/
├── main.py                     # FastAPI application entry point
├── pyproject.toml             # UV project configuration
├── fintrack-frontend/         # Next.js frontend
│   ├── app/                  # Next.js app router pages
│   ├── components/           # Reusable React components
│   ├── lib/                  # Utility functions and API clients
│   └── public/               # Static assets
├── src/                      # Backend source code
│   ├── routes/              # API route definitions
│   ├── services/            # Business logic services
│   ├── models/              # Data models and schemas
│   ├── agents/              # AI agent implementations
│   ├── llms/                # LLM integration modules
│   ├── nodes/               # LangGraph node definitions
│   ├── states/              # Workflow state management
│   └── graphs/              # LangGraph workflow definitions
└── logs/                    # Application logs
```

## 🚀 Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Project setup with UV package manager
- [x] FastAPI backend with route structure
- [x] Next.js frontend with React components
- [x] Basic API client and HTTP integration

### Phase 2: AI Agent Implementation 🔄
- [ ] LangGraph workflow definitions
- [ ] Individual agent implementations
- [ ] Agent communication protocols
- [ ] Multi-agent orchestration system

### Phase 3: Advanced Features 📋
- [ ] Database integration and models
- [ ] Authentication and security services
- [ ] ML model training and deployment
- [ ] Advanced analytics and reporting

### Phase 4: Production Readiness 📋
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [ ] Production deployment configuration
- [ ] Documentation and user guides

## 🤝 Contributing

This is a university assignment project. For academic integrity purposes, please refer to your institution's collaboration policies.

### Contributors

| IT Number | Name | Email |
| :---- | :---- | :---- |
| IT23270442 | Duwaragie K | it23270442@my.sliit.lk |
| IT23248212 | Zayan M.F.M | it23248212@my.sliit.lk |
| IT23212954 | Fonseka D.W.J.M | it23212954@my.sliit.lk |
| IT23151406 | Sandanayaka S.D.P.D | it23151406@my.sliit.lk |

## 📄 License

This project is created for educational purposes as part of a university assignment.

---

**Built with ❤️ using LangChain, LangGraph, FastAPI, and Next.js**

