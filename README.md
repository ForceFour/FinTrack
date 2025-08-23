# FinTrack - Financial Transaction Analysis System

A comprehensive financial transaction processing system built with **LangChain**, **LangGraph**, and **FastAPI** that processes raw transaction data through a 6-agent pipeline to provide intelligent financial insights and recommendations.

## 🏗️ Architecture Overview

The system implements a multi-agent architecture that processes transactions through 6 specialized agents:

```
RAW TRANSACTIONS → [1] INGESTION → [2] NER/MERCHANT → [3] CLASSIFIER → [4] PATTERN ANALYZER → [5] SUGGESTION → [6] SAFETY GUARD
```

### Agent Pipeline

1. **🔄 Ingestion Agent**: Normalizes raw data into structured fields
2. **🏪 NER/Merchant Agent**: Extracts and standardizes merchant information  
3. **🏷️ Classifier Agent**: Predicts expense categories using ML
4. **📊 Pattern Analyzer Agent**: Detects spending patterns and habits
5. **💡 Suggestion Agent**: Generates actionable financial recommendations
6. **🛡️ Safety Guard Agent**: Flags anomalies and security issues

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- uv package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fintrack
```

2. **Install dependencies with uv**
```bash
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the API server**
```bash
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Development Setup

**Install development dependencies:**
```bash
uv sync --extra dev
```

**Run tests:**
```bash
uv run pytest
```

**Format code:**
```bash
uv run black src tests
uv run isort src tests
```

## 📁 Project Structure

```
fintrack/
├── src/
│   ├── agents/                 # 6 specialized agents
│   │   ├── ingestion_agent.py
│   │   ├── ner_merchant_agent.py
│   │   ├── classifier_agent.py
│   │   ├── pattern_analyzer_agent.py
│   │   ├── suggestion_agent.py
│   │   └── safety_guard_agent.py
│   ├── api/                    # FastAPI application
│   │   └── main.py
│   ├── workflows/              # LangGraph workflows
│   │   └── transaction_workflow.py
│   ├── schemas/                # Pydantic data models
│   │   └── transaction_schemas.py
│   ├── models/                 # ML models
│   │   ├── category_classifier.py
│   │   └── anomaly_detector.py
│   └── utils/                  # Utility functions
│       ├── data_preprocessing.py
│       ├── ner_utils.py
│       └── feature_engineering.py
├── config/                     # Configuration
│   └── settings.py
├── tests/                      # Test suite
├── data/                       # Data storage
│   ├── raw/
│   └── processed/
├── docs/                       # Documentation
└── pyproject.toml             # Project configuration
```

## 🔌 API Endpoints

### Core Processing
- `POST /transactions/process` - Complete 6-agent pipeline
- `POST /transactions/ingest` - Ingestion agent only
- `POST /transactions/classify` - NER + Classification
- `POST /transactions/analyze` - Pattern analysis
- `POST /transactions/suggest` - Generate suggestions
- `POST /transactions/security-check` - Security validation

### Monitoring
- `GET /health` - Health check
- `GET /agents/status` - Agent status overview

## 🤖 Agent Details

### 1. Ingestion Agent
**Purpose**: Normalize raw transaction data
- Parse various date formats
- Convert amounts to numeric values
- Standardize payment methods
- Extract discount information
- Clean descriptions

### 2. NER/Merchant Agent  
**Purpose**: Extract merchant information
- Named Entity Recognition for merchants
- Standardize merchant names
- Map to merchant categories
- Handle unknown merchants

### 3. Classifier Agent
**Purpose**: Predict expense categories
- Feature engineering (numeric, text, categorical)
- ML-based category prediction
- Confidence scoring
- Support for model retraining

### 4. Pattern Analyzer Agent
**Purpose**: Detect spending patterns
- Identify recurring transactions
- Detect spending spikes
- Analyze monthly habits
- Generate actionable insights

### 5. Suggestion Agent
**Purpose**: Financial recommendations
- Budget optimization suggestions
- Spending reduction recommendations
- Subscription alerts
- Savings opportunities

### 6. Safety Guard Agent
**Purpose**: Security and compliance
- Anomaly detection
- Fraud indicators
- Spending limit validation
- Risk scoring

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Agent Orchestration**: LangChain + LangGraph
- **ML/Data**: scikit-learn, pandas, numpy
- **Data Validation**: Pydantic
- **Package Management**: uv
- **Testing**: pytest
- **Code Quality**: black, isort, flake8, mypy

## 📊 Usage Examples

### Process Raw Transactions

```python
import httpx

transactions = [
    {
        "id": "txn_001",
        "date": "2024-01-15",
        "amount": "$45.67",
        "description": "STARBUCKS STORE #1234",
        "payment_method": "Credit Card"
    }
]

response = httpx.post("http://localhost:8000/transactions/process", 
                     json=transactions)
result = response.json()
```

### Individual Agent Processing

```python
# Ingestion only
response = httpx.post("http://localhost:8000/transactions/ingest", 
                     json=transactions)

# Classification
response = httpx.post("http://localhost:8000/transactions/classify", 
                     json=preprocessed_transactions)
```

## 🔧 Configuration

Key configuration options in `config/settings.py`:

```python
# Agent timeouts and thresholds
agent_configs = {
    "classifier_agent": {
        "confidence_threshold": 0.7,
        "default_category": "miscellaneous"
    },
    "safety_guard_agent": {
        "anomaly_threshold": 0.9
    }
}
```

## 🧪 Testing

Run the complete test suite:
```bash
uv run pytest -v
```

Run specific test categories:
```bash
uv run pytest -m "unit"          # Unit tests only
uv run pytest -m "integration"   # Integration tests only
```

## 📈 Performance & Scalability

- **Batch Processing**: Handle up to 1000 transactions per request
- **Async Support**: Full async/await support throughout
- **Model Caching**: Trained models cached for performance
- **Horizontal Scaling**: Stateless design for easy scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Roadmap

- [ ] Database integration for transaction storage
- [ ] Real-time processing with WebSocket support
- [ ] Advanced ML models (deep learning)
- [ ] Multi-tenant support
- [ ] Dashboard and visualization
- [ ] Mobile app integration
- [ ] Cryptocurrency transaction support
