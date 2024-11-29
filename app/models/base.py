from sqlalchemy import func, TIMESTAMP
from sqlalchemy.orm import declarative_base, mapped_column
from typing_extensions import Annotated
import datetime
from enum import Enum
from typing import List, Type

timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.now()),
]

Base = declarative_base()

Base.type_annotation_map = {
    datetime.datetime: TIMESTAMP(timezone=True),
}


def get_enum_values(enum_cls: Type[Enum]) -> List[str]:
    """
    Retrieves the string values of all members of the given Enum class.

    Args:
        enum_cls (Type[Enum]): The Enum class to process.

    Returns:
        List[str]: A list of string values for the Enum members.
    """
    return [member.value for member in enum_cls]
