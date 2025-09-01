from sqlalchemy.orm import Session
import models.tables as tables

def login(db: Session, login: str, password: str):

    user = db.query(tables.users).filter(
        tables.users.Registration == login,
        tables.users.Password == password
    ).first()

    return user

def loadprojects(db: Session):
    projects = db.query(tables.projects).filter(
        tables.projects.Active == True
    ).all()
    return projects

def loadproducts(db: Session):
    products = db.query(tables.products).filter(
        tables.products.Active == True
    ).all()

    return products

def loadpartnumber(db: Session):
    partnumber = db.query(tables.partnumber).all()

    return partnumber

def loadprograms(db: Session):
    programas = db.query(tables.program_templates).all()
    return programas