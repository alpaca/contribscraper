from sqlalchemy import String, Column, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contributor(Base):
    __tablename__ = 'boe_contributors'

    id = Column(Integer, primary_key=True)
    contributed_by = Column(String)
    amount = Column(String)
    received_by = Column(Integer)
    description = Column(String)
    vendor_name = Column(String)
    vendor_address = Column(String)
    party = Column(String)
    address = Column(String)
    contrib_date = Column(Date)


class Committee(Base):
    __tablename__ = 'boe_democratic_committees'


    committee_name = Column(String)
    number = Column(Integer,primary_key = True)
