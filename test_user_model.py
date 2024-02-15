"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes
import sqlalchemy
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()
        db.session.execute(User.__table__.delete())
        Message.query.delete()
        Follows.query.delete()

        db.session.commit()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    def test_user_repr(self):
        u = User(
            email='email@email.com',
            username='anewuser',
            password='password'
        )
        
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(), f"<User #{u.id}: anewuser, email@email.com>")

    def test_user_signup(self):
        u = User.signup(username='someuser', email= 'email@email.com', password='password', image_url=None)

        db.session.commit()

        u= User.query.filter_by(username='someuser').first()

        self.assertEqual(u.email,"email@email.com")
        self.assertEqual(u.image_url,"/static/images/default-pic.png")
        self.assertTrue(bcrypt.check_password_hash(u.password,'password'))
    
    def test_username_unique_constraint(self):
        user1 = User(username='test_user', email='email@email.com', password='password')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='test_user', email='email@gmail.com', password='password')

        with self.assertRaises(Exception) as context:
            db.session.add(user2)
            db.session.commit()

        self.assertIsInstance(context.exception, sqlalchemy.exc.IntegrityError)

    def test_email_unique_constraint(self):
            user1 = User(username='test_user', email='email@email.com', password='password')
            db.session.add(user1)
            db.session.commit()

            user2 = User(username='testuser', email='email@email.com', password='password')

            with self.assertRaises(Exception) as context:
                db.session.add(user2)
                db.session.commit()

            self.assertIsInstance(context.exception, sqlalchemy.exc.IntegrityError)

    def test_user_authenticate(self):
        u = User.signup(username='someuser', email= 'email@email.com', password='password', image_url=None)

        db.session.commit()

        u= User.query.filter_by(username='someuser').first()

        self.assertEqual(u,User.authenticate(username='someuser', password='password'))
        self.assertFalse(User.authenticate(username='someuser', password='password1'))
        self.assertFalse(User.authenticate(username='someuser1', password='password'))

    def test_user_is_following(self):
        user1 = User(username='test_user', email='email@email.com', password='password')
        user2 = User(username='test_user2', email='email2@email.com', password='password')

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        user1 = User.query.filter_by(username='test_user').first()
        user2 = User.query.filter_by(username='test_user2').first()

        follows = Follows(user_being_followed_id = user1.id, user_following_id = user2.id)

        db.session.add(follows)
        db.session.commit()

        self.assertTrue(user2.is_following(user1))
        self.assertFalse(user1.is_following(user2))
    
    def test_user_is_followed_by(self):
        user1 = User(username='test_user', email='email@email.com', password='password')
        user2 = User(username='test_user2', email='email2@email.com', password='password')

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        user1 = User.query.filter_by(username='test_user').first()
        user2 = User.query.filter_by(username='test_user2').first()

        follows = Follows(user_being_followed_id = user1.id, user_following_id = user2.id)

        db.session.add(follows)
        db.session.commit()

        self.assertTrue(user1.is_followed_by(user2))
        self.assertFalse(user2.is_followed_by(user1))