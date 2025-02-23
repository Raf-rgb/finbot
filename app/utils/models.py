from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    CASH        = "Efectivo"
    DEBIT_CARD  = "Tarjeta de Débito"
    CREDIT_CARD = "Tarjeta de Crédito"
    VALE        = "Vales"

class MovementType(str, Enum):
    EXPENSE   = "Gasto"
    INCOME    = "Ingreso"

class Movement(BaseModel):
    name: str                   = Field(description="Nombre descriptivo al movimiento realizado")
    description: str            = Field(description="Descripción detallada al movimiento realizado")
    movement_type: MovementType = Field(description="Tipo de movimiento (Gasto o Ingreso)")
    amount: float               = Field(description="Cantidad de dinero involucrada en el movimiento")
    source_name: str            = Field("Efectivo", description="Fuenta de donde proviene el dinero")
    source_type: SourceType     = Field("Efectivo", description="Tipo de fuente de donde proviene el dinero")
    category: str               = Field(description="Categoria del movimiento")
    datetime: Optional[str]     = Field(None, description="Fecha y hora del movimiento (YYYY-MM-DD HH:MM:SS) si la proporciona el usuario")
