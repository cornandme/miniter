from flask import Flask, jsonify, request, current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
import bcrypt
from datetime import datetime, timedelta

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)

def get_user_by_id(user_id):
    user = current_app.database.execute(text("""
        SELECT
            *
        FROM
            users
        WHERE
            id = :user_id
        """), {
            'user_id': user_id
        }).fetchone()

def get_user_by_email(email):
    user = current_app.database.execute(text("""
        SELECT
            *
        FROM
            users
        WHERE
            id = :email
    """)).fetchone()
    
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile': user['profile']
    } if user else None

def insert_user(user):
    return current_app.database.execute(text("""
        INSERT INTO users (
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :name,
            :email,
            :profile,
            :password
        )
    """), user)

def insert_tweet(user_tweet):
    return current_app.database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            :user_id,
            :tweet
        )
    """), user_tweet)

# {user_id, follow}
def insert_follow(user_follow):
    return current_app.database.execute(text("""
        INSERT INTO users_follow_list (
            user_id,
            follow_user_id
        ) VALUES (
            :user_id,
            :follow
        )
    """), user_follow)

# {user_id, unfollow}
def delete_follow(user_unfollow):
    return current_app.database.execute(text("""
        DELETE FROM users_follow_list
        WHERE user_id=:user_id AND follow_user_id=:unfollow
    """), user_unfollow)

# {user_id}
def get_timeline(user_id):
    return current_app.database.execute(text("""
        SELECT
            t.user_id,
            t.tweet,
            t.created_at
        FROM 
            tweets AS t
            LEFT OUTER JOIN users_follow_list AS ufl 
            ON t.user_id = ufl.follow_user_id
        WHERE
            ufl.user_id = :user_id
            OR t.user_id = :user_id
        ORDER BY
            t.created_at DESC
    """), {'user_id': user_id})


def create_app(test_config = None):
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder
    
    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)
        
    database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0, echo=True)
    app.database = database

    @app.route("/ping", methods=["GET"])
    def ping():
        return "pong"

    # signup
    # {name, email, password, profile}
    @app.route("/sign-up", methods=["POST"])
    def sign_up():
        new_user = request.json
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode('UTF-8'),
            bcrypt.gensalt()
        )
        insert_result = insert_user(new_user)
        new_user_id = insert_result.lastrowid
        created_user = get_user_by_id(new_user_id)
        return jsonify({
            created_user['id'],
            created_user['name'],
            created_user['email'],
            created_user['profile']
        })

    @app.route("/login", methods=["POST"])
    def login():
        # request info
        credential = request.json
        email = credential['email']
        password = credential['password']

        # db user info
        user = get_user_by_email(email)
        user_credential = {
            'id': user['id'],
            'hashed_password': user['hashed_password']
        } if user else None

        # check password
        if user_credential and bcrypt.checkpw(password.encode('UTF-8'), user_credential['hashed_password'].encode('UTF-8')):
            # create token
            user_id = user_credential['id']
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')
            return jsonify({
                'access_token': token.decode('UTF-8')
            })
        else:
            return '', 401

    # tweet
    # {user_id, tweet}
    @app.route("/tweet", methods=["POST"])
    def tweet():
        # request 객체 받기
        user_tweet = request.json
        tweet = user_tweet['tweet']
        # 300자 초과인지 검사
        if len(tweet) > 300: 
            return 'too long tweet', 400
        # 트윗 저장
        insert_tweet(user_tweet)
        return '', 200

    # follow
    # {user_id, follow}
    @app.route("/follow", methods=["POST"])
    def follow():
        user_follow = request.json
        follow_info = insert_follow(user_follow).rowcount
        return '', 200

    # unfollow
    # {user_id, unfollow}
    @app.route("/unfollow", methods=["POST"])
    def unfollow():
        payload = request.json
        user_unfollow = request.json
        unfollow_info = delete_follow(user_unfollow).rowcount
        return '', 200

    # timeline
    # {user_id}
    @app.route("/timeline/<int:user_id>", methods=["GET"])
    def timeline(user_id):            
        timeline_info = get_timeline(user_id).fetchall()
        result = [{'user_id':tweet['user_id'],
                    'tweet':tweet['tweet'],
                    'created_at':tweet['created_at']} for tweet in timeline_info]
        return jsonify(result)

    return app