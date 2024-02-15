"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        db.session.commit()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 10
        self.testuser_id = 10

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_add_message_no_session(self):
        '''check to see that no message is created when not logged in'''
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(Message.query.filter_by(text='Hello').count(),0)
    
    def test_add_message_invalid_user(self):
        """check to see that no message is created if made"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 12345

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(Message.query.filter_by(text='Hello').count(),0)

    def test_show_messages(self):
        msg = Message(id=1515, text='abcd', user_id=self.testuser_id)
        db.session.add(msg)
        db.session.commit()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            
            m = Message.query.get(1515)

            resp = c.get('/messages/1515')
            
            self.assertEqual(resp.status_code,200)
            self.assertIn(m.text, str(resp.data))
    
    def test_show_invalid_message(self):
        with self.client as c:
            resp = c.get('/messages/99999999')

            self.assertEqual(resp.status_code,404)
    
    def test_delete_message(self):
        msg = Message(id=1515, text='abcd', user_id=self.testuser_id)
        db.session.add(msg)
        db.session.commit()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/messages/1515/delete', follow_redirects=True)
            testuser = User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(testuser.messages),0)

    def test_delete_message_no_login(self):
        msg = Message(id=1515, text='abcd', user_id=self.testuser_id)
        db.session.add(msg)
        db.session.commit()
        with self.client as c:
            resp = c.post('/messages/1515/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))

    def test_delete_message_wrong_user(self):
        msg = Message(id=1515, text='abcd', user_id=self.testuser_id)
        db.session.add(msg)
        usr = User(id=789, username='test', email='email@email.com', password='password')
        db.session.add(usr)
        db.session.commit()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 789
            resp = c.post('/messages/1515/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', str(resp.data))