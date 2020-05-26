import bcrypt
import time

import pytest
from sqlalchemy import create_engine, text

import config
from model import UserDAO, TweetDAO

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_dao():
    return UserDAO(database)

@pytest.fixture
def tweet_dao():
    return TweetDAO(database)

def setup_function():
    '''
    There is 3 users.
    User 2 has a tweet.
    User 3 follows user 2.
    '''
    # create 3 test users
    hashed_password_01 = bcrypt.hashpw(
        b'testpw01',
        bcrypt.gensalt()
    )
    hashed_password_02 = bcrypt.hashpw(
        b'testpw02',
        bcrypt.gensalt()
    )
    hashed_password_03 = bcrypt.hashpw(
        b'testpw03',
        bcrypt.gensalt()
    )

    new_users = [
        {
            'name': 'testname01',
            'email': 'test01@gmail.com',
            'profile': 'test profile 01',
            'hashed_password': hashed_password_01
        },
        {
            'name': 'testname02',
            'email': 'test02@gmail.com',
            'profile': 'test profile 02',
            'hashed_password': hashed_password_02
        },
        {
            'name': 'testname03',
            'email': 'test03@gmail.com',
            'profile': 'test profile 03',
            'hashed_password': hashed_password_03
        }
    ]
    database.execute(text("""
        INSERT INTO users (
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_users)

    # user 2 has a tweet
    tweet = {
        'user_id': 2,
        'tweet': 'test tweet user 2'
    }
    database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            :user_id,
            :tweet
        )
    """), tweet)

    # user 3 follows user 2
    follow = {
        'user_id': 3,
        'follow': 2
    }
    database.execute(text("""
        INSERT INTO users_follow_list (
            user_id,
            follow_user_id
        ) VALUES (
            :user_id,
            :follow
        )
    """), follow)
    time.sleep(1)

def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def test_insert_user(user_dao):
    # insert user 4
    new_user = {
        'name': 'testname04',
        'email': 'test04@gmail.com',
        'profile': 'test profile 04',
        'password': 'testpw04'
    }
    new_user_id = user_dao.insert_user(new_user).lastrowid

    # check if there is user 4 in DB
    row = database.execute(text("""
        SELECT
            id,
            name,
            email,
            profile
        FROM
            users
        WHERE
            id = :id
    """), {'id': new_user_id}).fetchone()

    row_dict = {
        'id': row['id'],
        'name': row['name'],
        'email': row['email'],
        'profile': row['profile']
    }
    assert row_dict == {
        'id': new_user_id,
        'name': new_user['name'],
        'email': new_user['email'],
        'profile': new_user['profile']
    }
    
def test_get_user_by_id(user_dao):
    # query user 1
    user = {
        'id': 1,
        'name': 'testname01',
        'email': 'test01@gmail.com',
        'profile': 'test profile 01'
    }
    row = user_dao.get_user_by_id(user['id'])
    row_dict = {
        'id': row['id'],
        'name': row['name'],
        'email': row['email'],
        'profile': row['profile']
    }

    # check the row matches
    assert row_dict == {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile': user['profile']
    }

def test_get_user_by_email(user_dao):
    # query user 1
    user = {
        'id': 1,
        'name': 'testname01',
        'email': 'test01@gmail.com',
        'profile': 'test profile 01'
    }
    row = user_dao.get_user_by_email(user['email'])
    row_dict = {
        'id': row['id'],
        'name': row['name'],
        'email': row['email'],
        'profile': row['profile']
    }
    hashed_password = row['hashed_password']

    # check the row matches
    assert row_dict == {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile': user['profile']
    }

    # check the encrypted password matches
    assert bcrypt.checkpw('testpw01'.encode('utf-8'), hashed_password.encode('utf-8'))

def test_insert_follow(user_dao):
    # user 1 follows user 2
    user_dao.insert_follow(1, 2)

    # check DB
    row = database.execute(text("""
        SELECT
            *
        FROM
            users_follow_list
        WHERE
            user_id = :user_id
    """), {'user_id': 1}).fetchone()
    assert row['follow_user_id'] == 2

def test_delete_follow(user_dao):
    # user 3 unfollows user 2
    user_dao.delete_follow(3, 2)

    # check DB
    row = database.execute(text("""
        SELECT
            *
        FROM
            users_follow_list
        WHERE
            user_id = :user_id
    """), {'user_id': 3}).fetchone()
    assert row == None

def test_insert_tweet(tweet_dao):
    # user 1 creates a tweet
    user_id = 1
    tweet = 'user 1 test tweet'
    tweet_dao.insert_tweet(user_id, tweet)

    # check DB
    row = database.execute(text("""
        SELECT
            *
        FROM
            tweets
        WHERE
            user_id = :user_id
    """), {'user_id': user_id}).fetchone()

    row_dict = {
        'user_id': row['user_id'],
        'tweet': row['tweet']
    }
    assert row_dict == {
        'user_id': 1,
        'tweet': tweet
    }

def test_get_timeline(tweet_dao):
    # user 3 creates a tweet
    user_id = 3
    tweet = 'user 3 test tweet'
    tweet_dao.insert_tweet(user_id, tweet)

    # load timeline: should be [user3's tweet, user2's tweet]
    timeline = tweet_dao.get_timeline(user_id).fetchall()
    
    timeline_dict = [{
        'user_id': tweet['user_id'],
        'tweet': tweet['tweet']
    } for tweet in timeline]

    assert timeline_dict == [
        {
            'user_id': 3,
            'tweet': 'user 3 test tweet'
        },
        {
            'user_id': 2,
            'tweet': 'test tweet user 2'
        }
    ]

def test_get_and_update_profile_picture(user_dao):
    # input
    user_id = 1
    image_url = 'https://miniter-static.s3.ap-northeast-2.amazonaws.com/profile_image/1.png'

    # get empty profile image
    result = user_dao.get_profile_picture(user_id)
    assert result is None

    # update profile image
    user_dao.update_profile_picture(image_url, user_id)
    
    result = database.execute(text("""
        SELECT
            *
        FROM
            users
        WHERE
            id = :user_id
    """), {'user_id': user_id}).fetchone()
    assert result['id'] == user_id
    assert result['profile_picture'] == image_url

    result = user_dao.get_profile_picture(user_id)
    assert result == image_url