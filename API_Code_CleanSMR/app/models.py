from app import db

class Observation(db.Model):
    __tablename__ = 'observations'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    timezone_offset = db.Column(db.Integer, nullable=True)
    coordinates = db.Column(db.String(255), nullable=True)
    water_temp = db.Column(db.Float, nullable=True)
    air_temp = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)
    wind_direction = db.Column(db.Float, nullable=True)
    precipitation = db.Column(db.Float, nullable=True)
    haze = db.Column(db.Float, nullable=True)
    becquerel = db.Column(db.Float, nullable=True)
    
    def __repr__(self):
        return f'<Observation {self.id}>'
