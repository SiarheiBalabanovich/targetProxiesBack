from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from config.database import Base

from sqlalchemy.types import TIMESTAMP


class Param(Base):
    __tablename__ = 'param'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    type = Column(String)
    description = Column(String)


class Endpoint(Base):
    __tablename__ = 'endpoint'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    api_endpoint = Column(String)
    successful_call = Column(JSON)

    params = relationship('EndpointParams', back_populates='endpoint')


class EndpointParams(Base):
    __tablename__ = 'endpoint_param'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    param_id = Column(Integer, ForeignKey(Param.id, ondelete='CASCADE'))
    endpoint_id = Column(Integer, ForeignKey(Endpoint.id, ondelete='CASCADE'))

    param = relationship('Param')
    endpoint = relationship('Endpoint')
