from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP
import datetime
from typing_extensions import Annotated



intpk = Annotated[int, mapped_column(primary_key=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Base(DeclarativeBase):
    type_annotation_map = {
        datetime.datetime: TIMESTAMP(timezone=True),
    }