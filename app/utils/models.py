from typing import Optional
from pydantic import BaseModel, Field

class Movement(BaseModel):
    name: str                   = Field(..., title="Nombre descriptivo del movimiento")
    description: Optional[str]  = Field(..., title="Describe el movimiento que el usuario ha realizado")
    movement_type: str          = Field(..., title="Tipo de movimiento (Gasto o Ingreso)")
    amount: float               = Field(..., title="Cantidad del movimiento")
    source: str                 = Field("Efectivo", title="Fuente del movimiento")
    category: str               = Field(..., title="Categoría del movimiento")
    datetime: Optional[str]     = Field(None, title="Fecha y hora del movimiento (YYYY-MM-DD HH:MM:SS)")