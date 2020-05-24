import json
import bcrypt
import time

import pytest
from sqlalchemy import create_engine, text

import config
from app import create_app

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api = app.test_client()

    return api

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

def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def test_ping(api):
    res = api.get('/ping')
    assert b'pong' in res.data

def test_login(api):
    # login user 1
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test01@gmail.com',
            'password': 'testpw01'
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 200
    assert b'access_token' in res.data

def test_signup(api):
    # signup user 4
    res = api.post(
        '/sign-up',
        data = json.dumps({
            'name': 'testname04',
            'email': 'test04@gmail.com',
            'password': 'testpw04',
            'profile': 'test profile 04'
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 200

    # login check
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test04@gmail.com',
            'password': 'testpw04'
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 200
    assert b"access_token" in res.data

def test_authorization(api):
    '''
    check if each endpoint returns 401 error
    when it gets a request without token or containing a wrong token
    '''
    
    # tweet
    res = api.post(
        '/tweet',
        data = json.dumps({
            'user_id': 1,
            'tweet': 'testing authorization'
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 401

    res = api.post(
        '/tweet',
        data = json.dumps({
            'user_id': 1,
            'tweet': 'testing authorization'
        }),
        content_type = 'application/json',
        headers = {'Authorization': 'faketoken'}
    )
    assert res.status_code == 401

    # follow
    res = api.post(
        '/follow',
        data = json.dumps({
            'user_id': 1,
            'follow': 2
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 401

    res = api.post(
        '/follow',
        data = json.dumps({
            'user_id': 1,
            'follow': 2
        }),
        content_type = 'application/json',
        headers = {'Authorization': 'faketoken'}
    )
    assert res.status_code == 401

    # unfollow
    res = api.post(
        '/unfollow',
        data = json.dumps({
            'user_id': 3,
            'unfollow': 2
        }),
        content_type = 'application/json'
    )
    assert res.status_code == 401

    res = api.post(
        '/unfollow',
        data = json.dumps({
            'user_id': 3,
            'unfollow': 2
        }),
        content_type = 'application/json',
        headers = {'Authorization': 'faketoken'}
    )
    assert res.status_code == 401

    # user_timeline
    res = api.get(
        '/timeline',
        content_type = 'application/json'
    )
    assert res.status_code == 401

    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': 'faketoken'}
    )
    assert res.status_code == 401

def test_tweet(api):
    # login user 1
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test01@gmail.com',
            'password': 'testpw01'
        }),
        content_type = 'application/json'
    )
    login_info = json.loads(res.data.decode('utf-8'))
    user_id = login_info['user_id']
    access_token = login_info['access_token']
    assert res.status_code == 200

    # create a tweet
    res = api.post(
        '/tweet',
        data = json.dumps({
            'user_id': user_id,
            'tweet': 'test tweet 01'
        }),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert res.status_code == 200

def test_timeline(api):
    # login user 1
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test01@gmail.com',
            'password': 'testpw01'
        }),
        content_type = 'application/json'
    )
    login_info = json.loads(res.data.decode('utf-8'))
    user_id = login_info['user_id']
    access_token = login_info['access_token']
    assert res.status_code == 200

    # create 2 tweets
    res = api.post(
        '/tweet',
        data = json.dumps({
            'user_id': user_id,
            'tweet': 'test tweet #1'
        }),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )

    time.sleep(1)

    res = api.post(
        '/tweet',
        data = json.dumps({
            'user_id': user_id,
            'tweet': 'test tweet #2'
        }),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )

    # load and check timeline content & order
    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert res.status_code == 200
    tweets = json.loads(res.data.decode('utf-8'))
    assert tweets['timeline'][0]['tweet'] == 'test tweet #2'
    assert tweets['timeline'][1]['tweet'] == 'test tweet #1'


def test_follow(api):
    # login user 1
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test01@gmail.com',
            'password': 'testpw01'
        }),
        content_type = 'application/json'
    )
    login_info = json.loads(res.data.decode('utf-8'))
    user_id = login_info['user_id']
    access_token = login_info['access_token']
    assert res.status_code == 200

    # check timeline if there is any tweet
    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    tweets = json.loads(res.data.decode('utf-8'))
    assert res.status_code == 200
    assert tweets == {
        'user_id': 1,
        'timeline': []
    }

    # follow user 2
    res = api.post(
        '/follow',
        data = json.dumps({'follow': 2}),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert res.status_code == 200

    # check timeline if there is a tweet of user 2
    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    tweets = json.loads(res.data.decode('utf-8'))
    assert res.status_code == 200

    following_user_id = tweets['timeline'][0]['user_id']
    assert following_user_id == 2

def test_unfollow(api):
    # login user 3
    res = api.post(
        '/login',
        data = json.dumps({
            'email': 'test03@gmail.com',
            'password': 'testpw03'
        }),
        content_type = 'application/json'
    )
    login_info = json.loads(res.data.decode('utf-8'))
    user_id = login_info['user_id']
    access_token = login_info['access_token']
    assert res.status_code == 200

    # check timeline if there is a tweet of user 2
    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    tweets = json.loads(res.data.decode('utf-8'))
    assert res.status_code == 200

    following_user_id = tweets['timeline'][0]['user_id']
    assert following_user_id == 2

    # unfollow user 2
    res = api.post(
        '/unfollow',
        data = json.dumps({'unfollow': 2}),
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    assert res.status_code == 200

    # check timeline if there is any tweet
    res = api.get(
        '/timeline',
        content_type = 'application/json',
        headers = {'Authorization': access_token}
    )
    tweets = json.loads(res.data.decode('utf-8'))
    assert res.status_code == 200
    assert tweets == {
        'user_id': 3,
        'timeline': []
    }
