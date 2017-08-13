#!/usr/bin/env python

# Item Catalog Project
# Udacity - Full Stack Nanodegree

# import dependencies and create Flask object "app"
from flask import Flask, render_template, url_for, request, \
                redirect, flash, jsonify

# import sqlalchemy dependencies
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

# import databases from database_setup file
from database_setup import Base, readingList, Book, User

# more flask imports for session tracking
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

from flask import make_response
import requests

app = Flask(__name__)

# store Client ID
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

# Define Application Name
APPLICATION_NAME = "Reading List"

# Connect to Database and create database session
engine = create_engine('sqlite:///readingListswithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# define login routing, include state variable


@app.route('/login/')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# define facebook login


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s" % access_token

    # Exchange client token for long-lived token
    app_id = json.loads(
        open(
            'fb_client_secrets.json',
            'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?grant_type='
           'fb_exchange_token&client_id=%s&client_secret=%s'
           '&fb_exchange_token=%s') % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.8/me'
    # Strip expire tage from access token
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = ('https://graph.facebook.com/v2.8/me?access_token=%s'
           '&fields=name,id,email') % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    print 'url sent for API access: %s' % url
    print 'API JSON result: %s' % result

    data = json.loads(result)

    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # The token must be stored in the login_session in order to logout
    login_session['access_token'] = token

    # Get user picture
    url = ('https://graph.facebook.com/v2.8/me/picture?access_token=%s'
           '&redirect=0&height=200&width=200') % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']
    print login_session['picture']

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<div></div>'
    flash("Now logged in as %s" % login_session['username'])
    return output

# define facebook disconnect


@app.route('/fbdisconnect/')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out."

# define google login routing


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."
                       ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # Check to see if user exists in database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<div></div>'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT = Revoke a current user's token and reset their login_session


@app.route('/gdisconnect/')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# Disconnect based on provider


@app.route('/disconnect/')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successsfully been logged out.")
        return redirect(url_for("showCategories"))
    else:
        flash("You were not logged in to begin with!")
        redirect(url_for("showCategories"))


# JSON API for Reading Lists and Books
@app.route('/reading-lists/<int:readingList_id>/JSON/')
def readingListJSON(readingList_id):
    reading_list = session.query(
        readingList).filter_by(id=readingList_id).one()
    books = session.query(Book).filter_by(readingList_id=readingList_id).all()
    return jsonify(Book=[i.serialize for i in books])


@app.route('/reading-lists/<int:readingList_id>/books/<int:book_id>/JSON/')
def bookItemJSON(readingList_id, book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    return jsonify(Book=book.serialize)


@app.route('/reading-lists/JSON/')
def allListsJSON():
    allLists = session.query(readingList).all()
    return jsonify(readingList=[i.serialize for i in allLists])


# This page is the landing page for all reading lists
@app.route('/')
@app.route('/reading-lists/')
def showCategories():
    allLists = session.query(readingList).order_by(asc(readingList.name))
    if 'username' not in login_session:
        return render_template('publiccategories.html', allLists=allLists)
    else:
        return render_template('categories.html', allLists=allLists)


# This page will allow users to create new categories
@app.route('/reading-lists/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['readingList-name']:
            name = request.form['readingList-name']
            newList = readingList(name=name, user_id=login_session['user_id'])
            session.add(newList)
            session.commit()
            flash("Successully created %s" % newList.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('new_category.html')


# This page allows users to edit an existing reading list
@app.route('/reading-lists/<int:readingList_id>/edit', methods=['GET', 'POST'])
def editCategory(readingList_id):
    book_list = session.query(readingList).filter_by(id=readingList_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if book_list.user_id != login_session['user_id']:
        flash('You are not authorized to edit this reading list.  '
              'Please create your own reading list in order to edit.')
        return render_template('notyourlist.html')
    if request.method == 'POST':
        if request.form['readingList-name']:
            name = request.form['readingList-name']
            book_list.name = name
            session.commit()
            flash("Successfully updated %s" % book_list.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('edit_category.html', readingList=book_list)


# This page allows users to delete an existing reading list
@app.route(
    '/reading-lists/<int:readingList_id>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteCategory(readingList_id):
    book_list = session.query(readingList).filter_by(id=readingList_id).one()
    list_name = book_list.name
    if 'username' not in login_session:
        return redirect('/login')
    if book_list.user_id != login_session['user_id']:
        flash('You are not authorized to delete this reading list.  '
              'Please create your own reading list in order to delete.')
        return render_template('notyourlist.html')
    if request.method == 'POST':
        if request.form['delete']:
            session.delete(book_list)
            session.commit()
            flash("%s deleted!" % list_name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('delete_category.html', readingList=book_list)


# This page will show items within a category
@app.route('/reading-lists/<int:list_id>/')
@app.route('/reading-lists/<int:list_id>/books/')
def showItems(list_id):
    book_list = session.query(readingList).filter_by(id=list_id).one()
    creator = getUserInfo(book_list.user_id)
    books = session.query(Book).filter_by(readingList_id=list_id).all()
    if 'username' not in login_session:
        return render_template(
            'publicitems.html',
            books=books,
            book_list=book_list,
            list_id=list_id,
            creator=creator)
    else:
        return render_template(
            'items.html',
            books=books,
            book_list=book_list,
            list_id=list_id,
            creator=creator)


# This page will let a user add an item to the category
@app.route('/reading-lists/<int:list_id>/books/new/', methods=['GET', 'POST'])
def newItem(list_id):
    book_list = session.query(readingList).filter_by(id=list_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if book_list.user_id != login_session['user_id']:
        flash('You are not authorized to add a book to this list.  '
              'Please create your own reading list in order to add items.')
        return render_template('notyourlist.html')
    if request.method == 'POST':
        if request.form['name']:
            new_book = Book(
                name=request.form['name'],
                author=request.form['author'],
                image=request.form['image'],
                description=request.form['description'],
                user_id=book_list.user_id,
                readingList_id=book_list.id)
            session.add(new_book)
            session.commit()
            flash("%s added!" % new_book.name)
            return redirect(url_for('showItems', list_id=list_id))
    else:
        return render_template(
            'new_item.html',
            list_id=list_id,
            list=book_list)


# This page will let a user edit a specifc item
@app.route(
    '/reading-lists/<int:list_id>/books/<int:book_id>/edit/',
    methods=[
        'GET',
        'POST'])
def editItem(list_id, book_id):
    editedBook = session.query(Book).filter_by(id=book_id).one()
    reading_list = session.query(readingList).filter_by(id=list_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if reading_list.user_id != login_session['user_id']:
        flash('You are not authorized to edit this book.  '
              'Please create your own reading list in order to edit books.')
        return render_template('notyourlist.html')
    if request.method == 'POST':
        if request.form['name']:
            editedBook.name = request.form['name']
        if request.form['author']:
            editedBook.author = request.form['author']
        if request.form['image']:
            editedBook.image = request.form['image']
        if request.form['description']:
            editedBook.description = request.form['description']
        session.add(editedBook)
        session.commit()
        flash('%s Successfully Updated!' % editedBook.name)
        return redirect(url_for('showItems', list_id=list_id))
    else:
        return render_template(
            'edit_item.html',
            list_id=list_id,
            book_id=book_id,
            item=editedBook,
            list=reading_list)


# This page will let a user delete a specific item
@app.route(
    '/reading-lists/<int:list_id>/books/<int:book_id>/delete/',
    methods=[
        'GET',
        'POST'])
def deleteItem(list_id, book_id):
    bookToDelete = session.query(Book).filter_by(id=book_id).one()
    reading_list = session.query(readingList).filter_by(id=list_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if reading_list.user_id != login_session['user_id']:
        flash('You are not authorized to delete this book.  '
              'Please create your own reading list in order to delete.')
        return render_template('notyourlist.html')
    if request.method == 'POST':
        session.delete(bookToDelete)
        session.commit()
        flash('%s Successfully Deleted!' % bookToDelete.name)
        return redirect(url_for('showItems', list_id=list_id))
    else:
        return render_template(
            'delete_item.html',
            book=bookToDelete,
            list_id=list_id,
            list=reading_list)


# Helper functions for login_sessions
def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = False
    app.run(host='0.0.0.0', port=5000)
