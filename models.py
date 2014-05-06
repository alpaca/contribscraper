from sqlalchemy import String, Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contributor(Base):
    __tablename__ = 'boe_contributors'

    id = Column(Integer, primary_key=True)
    contributed_by = Column(String)
    amount = Column(String)
    received_by = Column(String)
    description = Column(String)
    vendor_name = Column(String)
    vendor_address = Column(String)
    party = Column(String)