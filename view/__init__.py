import jwt
from functools import wraps

from flask import jsonify, request, current_app, Response, g
from flask.json import JSONEncoder
from flask_cors import CORS

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)

# decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                payload = None

            if payload is None:
                return Response(status=401)

            user_id = payload['user_id']
            g.user_id = user_id

        else:
            return Response(status=401)
        
        return f(*args, **kwargs)
    return decorated_function

def create_endpoints(app, services):
    app.json_encoder = CustomJSONEncoder

    user_service = services.user_service
    tweet_service = services.tweet_service

    # {'ping'}
    @app.route("/ping", methods=["GET"])
    def ping():
        return "pong"
    
    # {name, email, password, profile}
    @app.route("/sign-up", methods=["POST"])
    def sign_up():
        new_user = request.json
        new_user['password'] = user_service.encrypt_password(new_user['password'])
        insert_obj = user_service.create_new_user(new_user)
        created_user_id = user_service.get_created_user_id(insert_obj)
        created_user = user_service.get_user_by_id(created_user_id)

        return jsonify({
            'id': created_user['id'],
            'name': created_user['name'],
            'email': created_user['email'],
            'profile': created_user['profile']
        })

    # {email, password}
    @app.route("/login", methods=["POST"])
    def login():
        credential = request.json
        authorized, user_id = user_service.authorize(credential)
        
        if authorized:
            # user_id = user_service.get_user_id(credential['email'])
            token = user_service.generate_access_token(user_id)
            return jsonify({
                'user_id': user_id,
                'access_token': token
            })
        else:
            return '', 401

    # {tweet}
    @app.route("/tweet", methods=["POST"])
    @login_required
    def tweet():
        user_tweet = request.json
        user_id = g.user_id
        tweet = user_tweet['tweet']

        tweet_check_result = tweet_service.tweet_check(tweet)
        
        if tweet_check_result == 'ok':
            tweet_service.insert_tweet(user_id, tweet)
            return '', 200
        else:
            return tweet_check_result, 400

    # {follow}
    @app.route("/follow", methods=["POST"])
    @login_required
    def follow():
        user_follow = request.json
        user_id = g.user_id
        follow_id = user_follow['follow']

        user_service.follow(user_id, follow_id)
        return '', 200

    # {unfollow}
    @app.route("/unfollow", methods=["POST"])
    @login_required
    def unfollow():
        user_unfollow = request.json
        user_id = g.user_id
        unfollow_id = user_unfollow['unfollow']

        user_service.unfollow(user_id, unfollow_id)
        return '', 200

    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        timeline = tweet_service.get_timeline(user_id)
        return jsonify({
            'user_id': user_id,
            'timeline': timeline
        })

    @app.route("/timeline", methods=["GET"])
    @login_required
    def user_timeline():
        user_id = g.user_id
        timeline = tweet_service.get_timeline(user_id)
        return jsonify({
            'user_id': user_id,
            'timeline': timeline
        })