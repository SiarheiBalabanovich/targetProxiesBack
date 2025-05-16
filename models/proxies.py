from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from config.database import Base
from models.user import User


class Modem(Base):
    __tablename__ = 'modem'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)

    ip = Column(String, unique=True)
    port = Column(Integer, default=3000)
    login = Column(String)
    password = Column(String)
    proxy_port = Column(Integer)


class Proxy(Base):
    __tablename__ = 'proxy'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    modem_id = Column(Integer, ForeignKey(Modem.id))

    location = Column(String, default='German')

    http_key = Column(String, unique=True)
    http_ip = Column(String)
    http_port = Column(Integer)
    http_login = Column(String)
    http_password = Column(String)

    socks5_key = Column(String, unique=True)
    socks5_ip = Column(String)
    socks5_port = Column(Integer)
    socks5_login = Column(String)
    socks5_password = Column(String)

    auto_rotation = Column(Boolean, default=False)
    modem = relationship(Modem)
