from sqlalchemy import text

class TweetDAO:
    def __init__(self, database):
        self.database = database

    def insert_tweet(self, user_id, tweet):
        return self.database.execute(text("""
            INSERT INTO tweets (
                user_id,
                tweet
            ) VALUES (
                :user_id,
                :tweet
            )
        """), {
            'user_id': user_id,
            'tweet': tweet
        })

    def get_timeline(self, user_id):
        return self.database.execute(text("""
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