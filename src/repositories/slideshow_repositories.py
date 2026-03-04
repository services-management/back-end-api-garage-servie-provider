from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.repositories.base_repositories import BaseRepository
from src.schemas.slideshow import Slideshow
from src.core.enums import ServiceType

class SlideshowRepository(BaseRepository[Slideshow]):
    def __init__(self, db: Session):
        super().__init__(db, Slideshow)

    def get_by_service_type(self, service_type: ServiceType) -> List[Slideshow]:
        stmt = select(Slideshow).where(Slideshow.service_type == service_type)
        return list(self.db.execute(stmt).scalars().all())

    def create_slide(self, image_url: str, service_type: ServiceType) -> Slideshow:
        slide = Slideshow(image_url=image_url, service_type=service_type)
        self.db.add(slide)
        self.db.commit()
        self.db.refresh(slide)
        return slide
