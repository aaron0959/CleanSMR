from app import ma
from app.models import Observation

class ObservationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Observation
        load_instance = True
        include_fk = True
