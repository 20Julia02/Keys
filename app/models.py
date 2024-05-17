from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("position.id"), nullable=False)
    isGuest = Column(Boolean, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    faculty = relationship("Faculty")
    position = relationship("Position")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)


class Position(Base):
    __tablename__ = "position"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
