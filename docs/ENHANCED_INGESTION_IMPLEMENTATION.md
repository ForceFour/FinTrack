# Enhanced Ingestion Agent Implementation

## Overview

The Enhanced Ingestion Agent has been successfully implemented to handle both structured data (CSV/Excel files) and unstructured natural language input for transaction processing. This creates a unified entry point for all transaction data into the 6-agent pipeline.

## Architecture

### Before
```
Manual Entry (with defined fields) → Original Ingestion Agent → 6-Agent Pipeline
File Upload → Original Ingestion Agent → 6-Agent Pipeline
```

### After (Enhanced)
```
Manual NL Input → Enhanced Ingestion Agent (with NLP) → 6-Agent Pipeline → Save to DB
File Upload → Enhanced Ingestion Agent → 6-Agent Pipeline → Save to DB
Conversation → Enhanced Ingestion Agent (with Chat State) → 6-Agent Pipeline → Save to DB
```

## File Structure

```
src/agents/
├── ingestion_agent.py (ENHANCED - includes NL processing)
├── ner_merchant_agent.py (unchanged)
├── classifier_agent.py (unchanged)  
├── pattern_analyzer_agent.py (unchanged)
├── suggestion_agent.py (unchanged)
├── safety_guard_agent.py (unchanged)
└── components/
    ├── __init__.py
    ├── file_parser.py (handles structured CSV/Excel data)
    ├── nl_processor.py (handles natural language processing)
    └── conversation_manager.py (manages chat state and missing fields)

src/utils/
└── data_preprocessing.py (ENHANCED - comprehensive 7-step pipeline)
```

## Key Components

### 1. Enhanced Ingestion Agent (`ingestion_agent.py`)

**Main Class:** `EnhancedIngestionAgent`

**Input Types:**
- `structured`: For CSV/Excel/PDF file uploads  
- `unstructured`: For conversational natural language input (chat-based transaction entry)

**Key Features:**
- Unified preprocessing pipeline for all input types using comprehensive DataPreprocessor
- Date normalization (handles relative dates like "yesterday", "today")
- Amount parsing with multiple currency symbols
- Payment method standardization
- Discount extraction and calculation
- Outlier detection using IQR method
- Description cleaning

### 2. Comprehensive Data Preprocessor (`utils/data_preprocessing.py`)

**Purpose:** Implements the exact 7-step preprocessing pipeline used by all input types

**Pipeline Steps:**
1. **Cleanup**: Column normalization, drop unused columns (recurring_flag)
2. **Date Processing**: Extract year, month, day, day_of_week components
3. **Amount Handling**: IQR-based outlier detection, log transformation
4. **Discounts**: Extract percentages, calculate discount_value and effective_amount
5. **Encoding**: One-hot for categories/payment, frequency encoding for merchants
6. **Description Cleaning**: Text normalization (lowercase, remove numbers/special chars)
7. **Column Management**: Drop raw columns, rearrange in logical order

**Output Schema:**
```
['year','month','day','day_of_week','amount','is_outlier','amount_log',
 'discount_percent','discount_value','effective_amount','merchant_encoded','merchant',
 'offer_applied','pay_*','cat_*','description_clean']
```

### 3. File Parser Component (`components/file_parser.py`)

**Purpose:** Handle structured data from CSV/Excel files

**Features:**
- Column name normalization
- Required field validation
- Data type conversion
- Drops unnecessary columns (like `recurring_flag`)

### 4. NL Processor Component (`components/nl_processor.py`)

**Purpose:** Extract transaction information from natural language text

**Features:**
- LLM integration (Groq/Llama) when available
- Regex-based fallback extraction
- Field extraction: date, amount, merchant, payment method, discounts
- Confidence scoring
- Missing field detection

**Extracted Fields:**
- Date (with relative date support)
- Amount (with currency symbol handling)
- Description
- Merchant name
- Category
- Payment method
- Discounts/offers
- Location

### 5. Conversation Manager Component (`components/conversation_manager.py`)

**Purpose:** Manage interactive conversation flow for transaction entry

**Conversation States:**
- `INITIAL`: Starting state
- `EXTRACTING`: Processing input
- `PROMPTING_MISSING`: Asking for missing fields
- `CONFIRMING`: Showing extracted data for confirmation
- `COMPLETED`: Transaction ready for processing
- `ERROR`: Error state

**Features:**
- State management across conversation turns
- Missing field prompting
- Confirmation workflow
- Conversation history tracking

## API Usage

### 1. File Upload Processing

```python
from src.agents.ingestion_agent import EnhancedIngestionAgent, IngestionAgentInput
import pandas as pd

# Load CSV data
df = pd.read_csv('transactions.csv')

# Process through enhanced agent
agent = EnhancedIngestionAgent()
result = agent.process(IngestionAgentInput(
    input_type="structured",
    dataframe=df
))

# Get processed transactions
transactions = result.preprocessed_transactions
```

### 2. Natural Language Processing

```python
# Single natural language input
result = agent.process(IngestionAgentInput(
    input_type="unstructured",
    natural_language_input="I spent $25 at Starbucks yesterday using my credit card"
))

if result.preprocessed_transactions:
    # Transaction successfully processed
    transaction = result.preprocessed_transactions[0]
else:
    # Missing fields, need more info
    print(result.conversation_response)
```

### 3. Conversational Transaction Entry

```python
# Start conversation
conversation_state = None
user_input = "I bought coffee this morning"

result = agent.process(IngestionAgentInput(
    input_type="conversation",
    natural_language_input=user_input,
    conversation_context=conversation_state
))

print(result.conversation_response)  # "I need more information. What was the amount?"

# Continue conversation
conversation_state = result.conversation_state
user_input = "$5.50"

result = agent.process(IngestionAgentInput(
    input_type="conversation",
    natural_language_input=user_input,
    conversation_context=conversation_state
))

# Repeat until result.requires_user_input is False
```

### 4. Transaction Service Integration

```python
from src.services.transaction_service import TransactionService

service = TransactionService(db=db)

# For file uploads
result = await service.process_uploaded_transactions(df, user_id)

# For natural language input
result = await service.process_natural_language_transaction(
    user_input="I spent $25 at Starbucks yesterday",
    user_id=user_id
)
```

## Preprocessing Pipeline

The enhanced agent applies a comprehensive preprocessing pipeline:

### Step 1: Input Type Detection
- Structured: Normalize column names, validate data
- Unstructured: Extract fields using NLP/regex
- Conversation: Manage state and missing fields

### Step 2: Date Processing
- Parse various date formats
- Handle relative dates ("today", "yesterday")
- Extract date components (year, month, day, day_of_week)

### Step 3: Amount Handling
- Parse currency symbols (₹, $, €, £, ¥)
- Handle negative amounts
- Outlier detection using basic thresholds
- Log transformation for downstream analysis

### Step 4: Discount Processing
- Extract discount percentages from text
- Calculate discount values
- Compute effective amounts

### Step 5: Payment Method Standardization
- Map various payment method strings to standard enums
- Handle common variations and synonyms

### Step 6: Description Cleaning
- Remove extra whitespace
- Normalize special characters
- Preserve essential information

### Step 7: Schema Validation
- Ensure all required fields are present
- Convert to standard data types
- Create PreprocessedTransaction objects

## Integration with Existing Pipeline

The enhanced ingestion agent seamlessly integrates with the existing 6-agent pipeline:

1. **Enhanced Ingestion Agent** → Preprocesses and normalizes all input types
2. **NER/Merchant Agent** → Extracts merchant information
3. **Classifier Agent** → Categorizes transactions
4. **Pattern Analyzer Agent** → Identifies spending patterns
5. **Suggestion Agent** → Generates recommendations
6. **Safety Guard Agent** → Performs security checks

## Benefits

### For Users
- **Natural conversation**: No need to fill out forms
- **Flexible input**: "I spent $25 at Starbucks yesterday" works
- **Missing field prompts**: System asks for missing information
- **Confirmation**: Review extracted data before saving

### For Developers
- **Unified API**: Single agent handles all input types
- **Backward compatibility**: Existing pipeline unchanged
- **Modular design**: Components can be enhanced independently
- **Fallback support**: Works without LLM dependencies

### For System
- **Consistent data**: All inputs go through same preprocessing
- **Error handling**: Graceful degradation when components fail
- **Extensible**: Easy to add new input types or processing steps

## Consolidation Notes

**Preprocessing Unification (Completed):**
- Previously had duplicate preprocessing in `comprehensive_preprocessor.py` and `data_preprocessing.py`
- Consolidated all functionality into single `src/utils/data_preprocessing.py` file
- Both structured and unstructured inputs now use the same comprehensive 7-step pipeline
- Removed redundant `comprehensive_preprocessor.py` file to eliminate duplication
- Updated all imports in Enhanced Ingestion Agent to use unified preprocessor

**Benefits:**
- Single source of truth for preprocessing logic
- Consistent data processing across all input types
- Easier maintenance and updates
- Reduced code duplication

## Testing

Tests have been created to validate:
- ✅ Structured data processing (CSV/Excel)
- ✅ Natural language extraction (with fallback)
- ✅ Conversation state management
- ✅ Integration with transaction service
- ✅ Pipeline compatibility

Run tests with: `uv run python test_api_usage.py`

## Future Enhancements

1. **LLM Integration**: Add proper LangChain/Groq support for better NLP
2. **Voice Input**: Extend to handle speech-to-text input
3. **Image Processing**: Extract transaction data from receipt images
4. **Learning**: Improve extraction based on user corrections
5. **Multi-language**: Support for non-English transaction descriptions

## Configuration

The agent can be configured with:

```python
config = {
    'groq_api_key': 'your-groq-api-key',  # For enhanced NLP
    'date_formats': [...],                # Custom date formats
    'payment_mappings': {...},            # Custom payment method mappings
    'currency_symbols': [...],            # Supported currencies
}

agent = EnhancedIngestionAgent(config=config)
```

This implementation successfully addresses the requirement for natural language transaction entry while maintaining compatibility with existing file upload functionality and the downstream 6-agent pipeline.
