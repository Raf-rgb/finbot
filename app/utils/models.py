from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class MovementType(str, Enum):
    GASTO = "Gasto"
    INGRESO = "Ingreso"

class Movement(BaseModel):
    name: str                   = Field(description="Nombre descriptivo al movimiento realizado")
    description: str            = Field(description="Descripción detallada al movimiento realizado")
    movement_type: MovementType = Field(description="Tipo de movimiento (Gasto o Ingreso)")
    amount: float               = Field(description="Cantidad de dinero involucrada en el movimiento")
    source: str                 = Field("Efectivo", description="Fuenta de donde proviene el dinero")
    category: str               = Field(description="Categoria a la que pertenece el movimiento")
    datetime: Optional[str]     = Field(None, description="Fecha y hora del movimiento (YYYY-MM-DD HH:MM:SS) si la proporciona el usuario")
