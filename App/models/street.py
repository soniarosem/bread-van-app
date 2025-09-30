from App.database import db

class Street(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def get_json(self):
        return {"id": self.id, "name": self.name}

    def __repr__(self):
        return f"<Street {self.id} - {self.name}>"
