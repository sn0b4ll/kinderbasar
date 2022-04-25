from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean

engine = create_engine('sqlite:///test.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    uuid = Column(String, primary_key=True)
    name = Column(String)
    seller = Column(Integer)
    price = Column(String)
    sold = Column(String) # Was boolean, not working on development environment at least..

    def __repr__(self):
        return f"<Article(uuid='{self.uuid}', name='{self.name}', seller='{self.seller}', price='{self.price}, sold='{self.sold}'"

Base.metadata.create_all(engine)
session = Session()
