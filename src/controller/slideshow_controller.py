from typing import List
from sqlalchemy.orm import Session
from src.repositories.slideshow_repositories import SlideshowRepository
from src.core.enums import ServiceType
from src.schemas.slideshow import Slideshow

class SlideshowController:
    def __init__(self, db: Session):
        self.repo = SlideshowRepository(db)

    def get_slides_by_type(self, service_type: ServiceType) -> List[Slideshow]:
        return self.repo.get_by_service_type(service_type)

    def add_slide(self, image_url: str, service_type: ServiceType) -> Slideshow:
        return self.repo.create_slide(image_url, service_type)

    def delete_slide(self, slide_id: int) -> bool:
        slide = self.repo.get(slide_id)
        if not slide:
            return False
        self.repo.db.delete(slide)
        self.repo.db.commit()
        return True
