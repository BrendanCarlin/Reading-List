from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import readingList, Base, Book, User

engine = create_engine('sqlite:///readingListswithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all coversations with the database
# and represents a "staging zone" for all objects loaded into the
# database session object.  Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit().  If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create a dummy user
User1 = User(name='Brendan Literarian', email='brendan@noemail.com',
			 picture="http://http://findicons.com/files/icons/213/south_park/256/randy_marsh_head_icon_2.png")

# Create the Beach Reads reading list
beach_reads = readingList(user_id=1, name = "Beach Reads")

session.add(beach_reads)
session.commit()

# Add Books
beachRead1 = Book(user_id=1, name="Camino Island", image="https://images-na.ssl-images-amazon.com/images/I/512RnM56g6L._AC_US218_.jpg",
				  author="John Grisham", description="A gang of thieves stage a daring heist from a secure vault deep below Princeton University's Firestone Library.",
				  readingList=beach_reads)

session.add(beachRead1)
session.commit()

beachRead2 = Book(user_id=1, name = "The Late Show", image = "https://images-na.ssl-images-amazon.com/images/I/51b6oflEgHL._AC_US218_.jpg",
				  author = "Michael Connelly", description = "Introducing Renee Ballard, a fierce young detective fighting to prove herself on LAPD's toughest beat, from #1 New York Times bestselling author Michael Connelly.",
				  readingList = beach_reads)

session.add(beachRead2)
session.commit()

# Create the Sci-Fi and Fantasy reading list
sci_fi = readingList(user_id=1, name = "Science Fiction and Fantasy")

session.add(sci_fi)
session.commit()

# Add Books
sci_fiBook = Book(user_id=1, name = "Death's End (Remembrance of Earth's Past)",
				  image = "https://images-na.ssl-images-amazon.com/images/I/51fdj0QzTTL._AC_US218_.jpg",
				  author = "Cixin Liu and Ken Liu", description = "The New York Times bestselling conclusion to a tour de force near-future adventure trilogy from China's bestselling and beloved science fiction writer.",
				  readingList = sci_fi)

session.add(sci_fiBook)
session.commit()



print "Added Reading Lists and Books!"