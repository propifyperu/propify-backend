from common.models import BaseModel

class PropertyCondition(BaseModel):
    """
    Condición / etapa de la propiedad:
    - en construcción
    - estreno
    - antigüedad
    etc.
    """
    class Meta:
        db_table = "property_condition"
        ordering = ["name"]