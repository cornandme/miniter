from flask import Flask, jsonify, request
from flask.json import JSONEncoder
import time

app = Flask(__name__)

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

# user data
app.users = {}
# tweet data
app.tweets = []
# user id counter
app.id_count = 1


@app.route("/ping", methods=["GET"])
def ping():
    return "pong"

# signup
# {name, email, password}
@app.route("/sign-up", methods=["POST"])
def sign_up():
    new_user = request.json
    new_user['id'] = app.id_count
    app.users[app.id_count] = new_user
    app.id_count += 1
    return jsonify(new_user)

# tweet
# {user_id, tweet}
@app.route("/tweet", methods=["POST"])
def tweet():
    # request 객체 받기
    payload = request.json
    user_id = int(payload['user_id'])
    tweet = payload['tweet']
    # id가 있는지 검사
    if user_id not in app.users:
        return 'Not authorized user', 400
    # 300자 초과인지 검사
    if len(tweet) > 300: 
        return 'too long tweet', 400
    # 300자 이하 -> 트윗 저장
    payload['time'] = time.time()
    app.tweets.append(jsonify(payload))
    return '', 200

# follow
# {user_id, follow}
@app.route("/follow", methods=["POST"])
def follow():
    # request 객체 받기
    payload = request.json
    user_id = int(payload['user_id'])
    user_id_to_follow = int(payload['follow'])
    # user id와 target id가 user 테이블에 있는지 확인
    if user_id not in app.users:
        return "Not authorized user.", 400
    if user_id_to_follow not in app.users:
        return "You are following a ghost.", 400
    # target id를 follow 목록에 추가
    user = app.users[user_id]
    user.setdefault('tweet', set()).add(user_id_to_follow)
    return jsonify(user)


# unfollow
# {user_id, unfollow}
@app.route("/unfollow", methods=["POST"])
def unfollow():
    # request 객체 받기
    payload = request.json
    user_id = int(payload['user_id'])
    user_id_to_unfollow = int(payload['unfollow'])
    # user id와 target id가 user 테이블에 있는지 확인
    if user_id not in app.users:
        return "Not authorized user.", 400
    if user_id_to_unfollow not in app.users:
        return "You are already not following that ghost.", 400
    # target id를 follow 목록에서 제거
    user = app.users[user_id]
    user.setdefault('tweet', set()).discard(user_id_to_unfollow)
    return jsonify(user)


# timeline
# {user_id}
@app.route("/timeline/<int:user_id>", methods=["GET"])
def timeline(user_id):
    # id가 user 테이블에 있는지 확인
    if user_id not in app.users:
        return "Not authorized user.", 400
    # tweet 테이블에서, 요청 id 또는 follow set에 있는 id가 작성자인 트윗 가져오기
    valid_set = app.users[user_id].get('follow', set())
    valid_set.add(user_id)
    # todo: should solve this error
    timeline_li = [tweet for tweet in app.tweets if tweet['user_id'] in valid_set]
    return jsonify({
        'user_id': user_id,
        'timeline': timeline_li
    })