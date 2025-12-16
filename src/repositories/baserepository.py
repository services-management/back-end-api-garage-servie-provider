from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def get(self, id: int):
        return self.db.query(self.model).get(id)

    def list(self, skip: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id: int, data: dict):
        obj = self.get(id)
        if obj:
            for key, value in data.items():
                # specific check to ensure we only set valid attributes
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, obj):
        self.db.delete(obj)
        self.db.commit()