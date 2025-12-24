from sqlalchemy.orm import Session
from typing import TypeVar, Generic, Type, Any, Dict, List, Optional

# 1. Define the Type Variable (T represents your SQLAlchemy Model)
T = TypeVar("T")

# 2. Add Generic[T] to the class definition
class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id: int) -> Optional[T]:
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def add(self, obj: T) -> T:
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except Exception as e:
            self.db.rollback()
            raise e

    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        obj = self.get(id)
        if obj:
            for key, value in data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            try:
                self.db.commit()
                self.db.refresh(obj)
            except Exception as e:
                self.db.rollback()
                raise e
        return obj

    def delete(self, id: int) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False