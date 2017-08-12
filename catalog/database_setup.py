from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	picture = Column(String(250))

class readingList(Base):
	__tablename__ = 'readingList'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		"""Return object data in easily serializable format"""
		return {
			'name': self.name,
			'id'  : self.id,
			'user_id'   : self.user_id
		}

class Book(Base):
	__tablename__ = 'book'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	image = Column(String(250))
	author = Column(String(250))
	description = Column(String(250))
	readingList_id = Column(Integer, ForeignKey('readingList.id'))
	readingList = relationship(readingList)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		"""Return object data in easily serializable format"""
		return {
			'name':	self.name,
			'image': self.image,
			'author': self.author,
			'description': self.description
		}

engine = create_engine('sqlite:///readingListswithusers.db')

Base.metadata.create_all(engine)