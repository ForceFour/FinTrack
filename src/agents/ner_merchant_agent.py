"""
NER/Merchant Agent - Agent 2
Role: Extract merchant information and entities from transaction descriptions
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import PreprocessedTransaction, MerchantTransaction
from ..utils.ner_utils import MerchantExtractor


class NERMerchantAgentInput(BaseModel):
    """Input schema for NER/Merchant Agent"""
    preprocessed_transactions: List[PreprocessedTransaction] = Field(description="Preprocessed transaction data")


class NERMerchantAgentOutput(BaseModel):
    """Output schema for NER/Merchant Agent"""
    merchant_transactions: List[MerchantTransaction] = Field(description="Transactions with merchant info")
    merchant_mapping: Dict[str, str] = Field(description="Merchant name mappings")


class NERMerchantAgent:
    """
    Agent 2: NER/Merchant Agent
    
    Responsibilities:
    - Extract merchant names from transaction descriptions using NER
    - Standardize merchant names (e.g., "STARBUCKS #1234" -> "Starbucks")
    - Map merchants to categories when possible
    - Handle unknown merchants by mapping to "Miscellaneous"
    - Maintain merchant name consistency across transactions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.merchant_extractor = MerchantExtractor()
        self.merchant_mapping = {}
    
    def extract_merchant_name(self, description: str) -> Optional[str]:
        """Extract merchant name from transaction description"""
        # Implementation for merchant name extraction using NER
        pass
    
    def standardize_merchant_name(self, merchant_name: str) -> str:
        """Standardize merchant name format"""
        # Implementation for merchant name standardization
        pass
    
    def get_merchant_category(self, merchant_name: str) -> Optional[str]:
        """Get merchant category if available"""
        # Implementation for merchant category mapping
        pass
    
    def update_merchant_mapping(self, original: str, standardized: str):
        """Update internal merchant mapping"""
        self.merchant_mapping[original] = standardized
    
    def process(self, input_data: NERMerchantAgentInput) -> NERMerchantAgentOutput:
        """Main processing method for the NER/Merchant Agent"""
        # Implementation for processing merchant information
        pass
