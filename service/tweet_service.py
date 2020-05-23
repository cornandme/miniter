

class TweetService:
    def __init__(self, tweet_dao):
        self.tweet_dao = tweet_dao

    def tweet_check(self, tweet):
        if len(tweet) > 300:
            return 'Too long tweet.', 400
        return 'ok'

    def insert_tweet(self, user_id, tweet):
        self.tweet_dao.insert_tweet(user_id, tweet)

    def get_timeline(self, user_id):
        raw_timeline = self.tweet_dao.get_timeline(user_id).fetchall()
        timeline = [{'tweet': tweet['tweet'],
                    'user_id': tweet['user_id'],
                    'created_at': tweet['created_at']} for tweet in raw_timeline]
        return timeline