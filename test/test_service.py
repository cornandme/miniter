import bcrypt
import jwt
import time

import pytest
from sqlalchemy import create_engine, text
from unittest import mock

import config
from model import UserDAO, TweetDAO
from service import UserService, TweetService

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_service():
    mock_s3_client = mock.Mock()
    return UserService(UserDAO(database), config.test_config, mock_s3_client)

@pytest.fixture
def tweet_service():
    return TweetService(TweetDAO(database))

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

def test_encrypt_password(user_service):
    pass

def test_create_new_user(user_service):
    pass

def test_get_created_user_id(user_service):
    pass

def test_get_user_by_id(user_service):
    pass

def test_authorize(user_service):
    # case 1: use user 1's credential
    credential = {
        'email': 'test01@gmail.com',
        'password': 'testpw01'
    }
    authorized, user_id = user_service.authorize(credential)
    assert authorized == True
    assert user_id == 1

    # case 2: correct email, fake password
    credential = {
        'email': 'test01@gmail.com',
        'password': 'fakepw'
    }
    authorized, user_id = user_service.authorize(credential)
    assert authorized == False
    assert user_id == 1

    # case 3: false email
    credential = {
        'email': 'rainbow@yahoo.co.kr',
        'password': 'yaho'
    }
    authorized, user_id = user_service.authorize(credential)
    assert authorized == False
    assert user_id == False

def test_get_user_id(user_service):
    # user 1
    email = 'test01@gmail.com'
    result = user_service.get_user_id(email)
    assert result == 1

def test_generate_access_token(user_service):
    # user 1
    user_id = 1
    token = user_service.generate_access_token(user_id)
    decoded = jwt.decode(token, config.JWT_SECRET_KEY, 'HS256')
    assert decoded['user_id'] == user_id

def test_follow(user_service):
    pass

def test_unfollow(user_service):
    pass

def test_tweet_check(tweet_service):
    # text length check
    tweet = '1' * 300
    result = tweet_service.tweet_check(tweet)
    assert result == 'ok'

    tweet = '1' * 301
    result = tweet_service.tweet_check(tweet)
    assert result == 'Too long tweet.'

def test_insert_tweet(tweet_service):
    pass

def test_get_timeline(tweet_service):
    pass

def test_get_and_save_profile_picture(user_service):
    # input
    user_id = 1
    test_pic = mock.Mock()
    image_url = f"{config.test_config['S3_BUCKET_URL']}{'profile_image/'}{user_id}{'.png'}"

    # get empty url
    result = user_service.get_profile_picture(user_id)
    assert result is None

    # save picture
    user_service.save_profile_picture(test_pic, user_id)

    # get url
    result = user_service.get_profile_picture(user_id)
    assert result == image_url