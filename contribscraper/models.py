from sqlalchemy import String, Column, Integer, Date, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def make_contributor_model(base):
    class Contributor(base):
        __tablename__ = 'boe_contributors'

        id = Column(Integer, primary_key=True)
        contributed_by = Column(String)
        amount = Column(String)
        received_by = Column(Integer)
        description = Column(String)
        vendor_name = Column(String)
        vendor_address = Column(String)
        party = Column(String)
        contributor_address = Column(String)
        contributor_addr_lat = Column(Float)
        contributor_addr_lng = Column(Float)
        zipcode = Column(Integer)
        contrib_date = Column(Date)
    return Contributor

def make_committee_model(base):
    class Committee(base):
        __tablename__ = 'boe_democratic_committees'

        committee_name = Column(String)
        number = Column(Integer,primary_key = True)
    return Committee

Contributor = make_contributor_model(Base)
Committee = make_committee_model(Base)