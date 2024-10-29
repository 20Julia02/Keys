from sqlalchemy import func, TIMESTAMP
from sqlalchemy.orm import declarative_base, mapped_column
from typing_extensions import Annotated
import datetime

timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.now()),
]

Base = declarative_base()

Base.type_annotation_map = {
    datetime.datetime: TIMESTAMP(timezone=True),
}
