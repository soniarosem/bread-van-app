from App.database import db


class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    street_id = db.Column(db.Integer, db.ForeignKey("street.id"), nullable=False)
    address = db.Column(db.String(120), nullable=False)

    user = db.relationship("User", backref=db.backref("resident_profile", uselist=False))
    street = db.relationship("Street", backref="residents")

    def get_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "street_id": self.street_id,
            "address": self.address
        }

    def __repr__(self):
        return f"<Resident {self.id} (user:{self.user_id}) at {self.address}>"




