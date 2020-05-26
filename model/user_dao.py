from sqlalchemy import text

class UserDAO:
    def __init__(self, database):
        self.database = database

    def insert_user(self, new_user):
        return self.database.execute(text("""
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
        """), new_user)

    def get_user_by_id(self, created_user_id):
        return self.database.execute(text("""
            SELECT
                *
            FROM
                users
            WHERE
                id = :user_id
            """), {'user_id': created_user_id}).fetchone()

    def get_user_by_email(self, email):
        return self.database.execute(text("""
            SELECT
                *
            FROM
                users
            WHERE
                email = :email
        """), {'email': email}).fetchone()

    def insert_follow(self, user_id, follow_id):
        return self.database.execute(text("""
            INSERT INTO users_follow_list (
                user_id,
                follow_user_id
            ) VALUES (
                :user_id,
                :follow
            )
        """), {
            'user_id': user_id,
            'follow': follow_id
        })

    def delete_follow(self, user_id, unfollow_id):
        return self.database.execute(text("""
            DELETE FROM users_follow_list
            WHERE user_id=:user_id AND follow_user_id=:unfollow
        """), {
            'user_id': user_id,
            'unfollow': unfollow_id
        })

    def update_profile_picture(self, image_url, user_id):
        return self.database.execute(text("""
            UPDATE users
            SET profile_picture = :image_url
            WHERE id = :user_id
        """), {
            'user_id': user_id,
            'image_url': image_url
        })

    def get_profile_picture(self, user_id):
        row = self.database.execute(text("""
            SELECT
                profile_picture
            FROM
                users
            WHERE
                id = :user_id
        """), {'user_id': user_id}).fetchone()

        return row['profile_picture'] if row else None