from datetime import datetime
from App.database import db


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver.id"), nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("street.id"), nullable=False)
    arrive_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="SCHEDULED", nullable=False)  # SCHEDULED|EN_ROUTE|ARRIVED|COMPLETE|CANCELLED

    driver = db.relationship("Driver", backref="drives")
    street = db.relationship("Street", backref="drives")

    def get_json(self):
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "street_id": self.street_id,
            "arrive_at": self.arrive_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }

    def __repr__(self):
        return f"<Drive {self.id} - Driver {self.driver_id} to Street {self.street_id} at {self.arrive_at}>"




