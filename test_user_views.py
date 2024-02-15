"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

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


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 0
        self.testuser.id = 0
        self.u1 = User.signup("usr1", "email1@email.com", "password", None)
        self.u1_id = 10
        self.u1.id = 10
        self.u2 = User.signup("usr2", "email2@email.com", "password", None)
        self.u2_id = 20
        self.u2.id = 20
        self.u3 = User.signup("usr3", "email3@email.com", "password", None)
        self.u3_id = 30
        self.u3.id = 30
        self.u4 = User.signup("usr4", "email4@email.com", "password", None)
        self.u4_id = 40
        self.u4.id = 40

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_list(self):
        """Show all users"""

        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@usr1", str(resp.data))
            self.assertIn("@usr2", str(resp.data))
            self.assertIn("@usr3", str(resp.data))
            self.assertIn("@usr4", str(resp.data))
    
    def test_user_search(self):
        '''check to see that user search is properly filtering users'''
        with self.client as c:
            resp = c.get("/users?q=usr")

            self.assertIn('@usr1',str(resp.data))
            self.assertIn('@usr2',str(resp.data))
            self.assertIn('@usr3',str(resp.data))
            self.assertIn('@usr4',str(resp.data))

            self.assertNotIn('testuser',str(resp.data))

    def test_user_details(self):
        """check to see if user details are coming up for the right user"""
        with self.client as c:
            resp = c.get('/users/10')

            self.assertEqual(resp.status_code,200)
            self.assertIn('usr1', str(resp.data))
            self.assertIn('Following', str(resp.data))
            self.assertIn('Followers', str(resp.data))
            self.assertIn('Likes', str(resp.data))
            self.assertIn('Messages', str(resp.data))

    def test_add_like(self):
        """test to see if user like works with user logged in"""
        m1 = Message(id=12345, text='abc', user_id=self.u1_id)
        m2 = Message(id=23456, text='xyz', user_id=self.u1_id)
        db.session.add_all([m1,m2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.post('/users/add_like/12345')
            testuser = User.query.get(self.testuser_id)
            likes = testuser.likes

            self.assertEqual(resp.status_code,302)
            self.assertEqual(len(likes),1)
            self.assertEqual(likes[0].id,12345)
    
    def test_remove_like(self):
        """test to see if user unlike works with user logged in"""
        m1 = Message(id=12345, text='abc', user_id=self.u1_id)
        m2 = Message(id=23456, text='xyz', user_id=self.u1_id)
        db.session.add_all([m1,m2])
        db.session.commit()
        newlike1 = Likes(user_id=self.testuser_id, message_id=12345)
        newlike2 = Likes(user_id=self.testuser_id, message_id=23456)
        db.session.add_all([newlike1, newlike2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.post('/users/add_like/12345')
            testuser = User.query.get(self.testuser_id)
            likes = testuser.likes

            self.assertEqual(resp.status_code,302)
            self.assertEqual(len(likes),1)
            self.assertEqual(likes[0].id, 23456)

    def test_show_likes(self):
        m1 = Message(id=12345, text='abc', user_id=self.u1_id)
        m2 = Message(id=23456, text='xyz', user_id=self.u1_id)
        db.session.add_all([m1,m2])
        db.session.commit()
        newlike = Likes(user_id=self.testuser_id, message_id=12345)
        db.session.add(newlike)
        db.session.commit()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}/likes')

            self.assertIn('abc', str(resp.data))
            self.assertNotIn('xyz', str(resp.data))
            self.assertIn('1', str(resp.data))
    
    def test_add_like_no_login(self):
        """test to see if user like fails with user not logged in"""
        m1 = Message(id=12345, text='abc', user_id=self.u1_id)
        m2 = Message(id=23456, text='xyz', user_id=self.u1_id)
        db.session.add_all([m1,m2])
        db.session.commit()
        newlike = Likes(user_id=self.testuser_id, message_id=23456)
        db.session.add(newlike)
        db.session.commit()

        with self.client as c:
            resp = c.post('/users/add_like/12345', follow_redirects=True)
            testuser = User.query.get(self.testuser_id)
            likes = testuser.likes

            self.assertEqual(resp.status_code,200)
            self.assertEqual(len(likes),1)
            self.assertIn('Must be logged in to like a warble.', str(resp.data))
    
    def test_show_user_follows(self):
        """test to see if following shows correctly when logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp=c.get(f'/users/{self.testuser_id}/following')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@usr3', str(resp.data))
            self.assertIn('@usr4', str(resp.data))
            self.assertNotIn('@usr1', str(resp.data))
            self.assertNotIn('@usr2', str(resp.data))
            self.assertIn('2', str(resp.data))

    def test_show_user_followers(self):
        """test to see if followers show correctly when logged in"""
        f1 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u4_id)
        f2 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u3_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp=c.get(f'/users/{self.testuser_id}/followers')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@usr3', str(resp.data))
            self.assertIn('@usr4', str(resp.data))
            self.assertNotIn('@usr1', str(resp.data))
            self.assertNotIn('@usr2', str(resp.data))
            self.assertIn('2', str(resp.data))

    def test_show_user_follows_no_login(self):
        """test to see if following redirects correctly when not logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            resp=c.get(f'/users/{self.testuser_id}/following', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            

    def test_show_user_followers_no_login(self):
        """test to see if followers redirects correctly when not logged in"""
        f1 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u4_id)
        f2 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u3_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            resp=c.get(f'/users/{self.testuser_id}/followers', follow_redirects=True)

            self.assertEqual(resp.status_code,200)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_user_add_follow(self):
        """test to see if follows add correctly when logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        db.session.add(f1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.post(f'/users/follow/{self.u3_id}', follow_redirects=True)
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(testuser.following), 2)
            self.assertIn('@usr3', str(resp.data))
            self.assertIn('@usr4', str(resp.data))
            self.assertNotIn('@usr1', str(resp.data))
            self.assertNotIn('@usr2', str(resp.data))
    
    def test_user_delete_follow(self):
        """test to see if follows delete correctly when logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp=c.post(f'/users/stop-following/{self.u4_id}', follow_redirects=True)
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(testuser.following), 1)
            self.assertIn('@usr3', str(resp.data))
            self.assertNotIn('@usr4', str(resp.data))
            self.assertNotIn('@usr1', str(resp.data))
            self.assertNotIn('@usr2', str(resp.data))
    
    def test_user_add_follow_invalid(self):
        """test to see if 404s correctly when following invalid user"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        db.session.add(f1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.post(f'/users/follow/99999999999999')
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 404)
            self.assertEqual(len(testuser.following), 1)

    def test_user_delete_follow_invalid(self):
        """test to see if 404s correctly when deleting invalid follow logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp=c.post('/users/stop-following/99999999999')
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 500)
            self.assertEqual(len(testuser.following), 2)

    def test_user_add_follow_no_login(self):
        """test to see if redirects correctly when adding follow while not logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        db.session.add(f1)
        db.session.commit()

        with self.client as c:
            resp = c.post(f'/users/follow/{self.u3_id}', follow_redirects=True)
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(testuser.following), 1)
            self.assertIn("Access unauthorized.", str(resp.data))

    def test_user_delete_follow_no_login(self):
        """test to see if redirects correctly when deleting follow while not logged in"""
        f1 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)

        db.session.add_all([f1,f2])
        db.session.commit()

        with self.client as c:
            resp=c.post(f'/users/stop-following/{self.u4_id}', follow_redirects=True)
            testuser= User.query.get(self.testuser_id)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(testuser.following), 2)
            self.assertIn('Access unauthorized.', str(resp.data))
