from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"

    unique_patient_id = Column(String, primary_key=True, index=True)
    full_name         = Column(String)
    date_of_birth     = Column(String)
    gender            = Column(String)
