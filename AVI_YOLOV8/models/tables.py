from sqlalchemy import Column, Integer, String, DateTime, Boolean as bool
from database import Base

class users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    Registration = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=False)  # senha criptografada

class program_templates(Base):
    __tablename__ = "program_templates"

    id = Column(Integer, primary_key=True, index=True)
    IdProject = Column(Integer, index=True)
    IdProduct = Column(Integer, index=True)
    IdUser = Column(Integer, index=True)
    Active = Column(bool, index=True)
    DateCreate = Column(DateTime, unique=True, nullable=False)
    Description = Column(String, nullable=False)


class projects(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    Description = Column(String)
    Active = Column(bool, index=True)

class products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    IdProject = Column(Integer, index=True)
    Active = Column(bool, index=True)
    Description = Column(String)

class partnumber(Base):
    __tablename__ = "product_part_numbers"

    id = Column(Integer, primary_key=True, index=True)
    IdProject = Column(Integer, index=True)
    IdProduct = Column(Integer, index=True)
    PartNumber = Column(String)
