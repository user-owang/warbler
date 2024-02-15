"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes
from flask_bcrypt import Bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()
        u = User(
            id=10,
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        
        self.user = User.query.filter_by(username='testuser').first
        self.user_id = 10

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""
        tweet = Message(text='abc', user_id=self.user_id)
        
        db.session.add(tweet)
        db.session.commit()
        
        twit = Message.query.filter_by(user_id=self.user_id).first()
        user = User.query.get(self.user_id)

        self.assertEqual(len(user.messages), 1)
        self.assertEqual(twit.text, 'abc')
    
    def test_message_likes(self):
        u = User(
            email='email@email.com',
            username='anewuser',
            password='password'
        )
        db.session.add(u)
        tweet= Message(text='abcd', user_id=self.user_id)
        db.session.add(tweet)

        db.session.commit()
        usr = User.query.filter_by(username='anewuser').first()
        twit= Message.query.filter_by(user_id=self.user_id).first()

        newlike = Likes(message_id=twit.id, user_id=usr.id)
        db.session.add(newlike)
        db.session.commit()


        self.assertEqual(len(usr.likes), 1)
        self.assertIn('abcd', [l.text for l in usr.likes])