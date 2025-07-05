from pydantic import BaseModel, Field, ConfigDict


class OffChainSchema(BaseModel):
    name: str
    version: str
    description: str
    dialect: str
    schema_content: str = Field(..., alias="schema")  # Use aliases to avoid conflicts

    model_config = ConfigDict(validate_by_name=True)