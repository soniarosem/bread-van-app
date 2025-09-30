from datetime import datetime
from App.database import db


class StopRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("resident.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="PENDING", nullable=False)  # PENDING|CONFIRMED|CANCELLED|COMPLETED
    address = db.Column(db.String(200), nullable=False)

    resident = db.relationship("Resident", backref="stop_requests")
    drive = db.relationship("Drive", backref="stop_requests")

    def get_json(self):
        return {
            "id": self.id,
            "resident_id": self.resident_id,
            "drive_id": self.drive_id,
            "requested_at": self.requested_at.isoformat(),
            "status": self.status,
            "address": self.address
        }

    def __repr__(self):
        return f"<StopRequest {self.id} - Resident {self.resident_id} for Drive {self.drive_id}>"