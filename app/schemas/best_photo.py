from pydantic import BaseModel, ConfigDict
from datetime import date
from .photo import PhotoOut
from .base import BaseModelConfig

class BestPhotoOut(BaseModel):
    model_config: ConfigDict = BaseModelConfig
    date:  date
    photo: PhotoOut

    @classmethod
    def from_orm(cls, record):
        # record has .photo and .date
        return cls(
            date=record.date,
            photo=PhotoOut.model_validate(record.photo)
        )
