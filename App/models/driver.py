from App.database import db
from datetime import datetime

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    status = db.Column(db.String(20), default="OFF_DUTY", nullable=False)  # OFF_DUTY|EN_ROUTE|DELAYED|COMPLETE
    location = db.Column(db.String(120), default="UNSPECIFIED", nullable=False)
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("driver_profile", uselist=False))

    def get_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "location": self.location,
            "status_updated_at": self.status_updated_at.isoformat()
        }

    def __repr__(self):
        return f"<Driver {self.id} (user:{self.user_id}) {self.status}@{self.location}>"
