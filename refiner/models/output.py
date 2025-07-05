from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from refiner.models.offchain_schema import OffChainSchema


class Output(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    
    refinement_url: Optional[str] = None
    schema_content: Optional[OffChainSchema] = Field(None, alias="schema")  # Use aliases to avoid conflicts
