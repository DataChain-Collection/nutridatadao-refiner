from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ColumnDefinition(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    description: Optional[str] = None

class TableDefinition(BaseModel):
    name: str
    columns: List[Dict[str, Any]]
    description: Optional[str] = None

class RelationshipDefinition(BaseModel):
    name: str
    source_table: str
    target_table: str
    source_column: str
    target_column: str
    type: str = "one-to-many"

class OffChainSchema(BaseModel):
    name: str
    version: str
    description: str
    dialect: str
    tables: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]