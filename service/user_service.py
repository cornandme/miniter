import os
import jwt
import bcrypt

from datetime   import datetime, timedelta

class UserService:
    def __init__(self, user_dao, config, s3_client):
        self.user_dao = user_dao
        self.config = config
        self.s3 = s3_client

    def encrypt_password(self, password):
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

    def create_new_user(self, new_user):
        return self.user_dao.insert_user(new_user)

    def get_created_user_id(self, insert_obj):
        return insert_obj.lastrowid

    def get_user_by_id(self, created_user_id):
        return self.user_dao.get_user_by_id(created_user_id)

    def authorize(self, credential):
        email = credential['email']
        password = credential['password']
        
        user = self.user_dao.get_user_by_email(email)
        user_credential = {
            'id': user['id'],
            'hashed_password': user['hashed_password']
        } if user else False

        user_id = user['id'] if user else False
        authorized = user_credential and bcrypt.checkpw(password.encode('utf-8'), user_credential['hashed_password'].encode('utf-8'))
        return authorized, user_id

    def get_user_id(self, email):
        user = self.user_dao.get_user_by_email(email)
        user_id = user['id']
        return user_id

    def generate_access_token(self, user_id):
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds = 60 * 60 * 24)
        }
        token = jwt.encode(
            payload, 
            self.config['JWT_SECRET_KEY'], 
            'HS256'
        )
        return token.decode('utf-8')

    def follow(self, user_id, follow_id):
        self.user_dao.insert_follow(user_id, follow_id)

    def unfollow(self, user_id, unfollow_id):
        self.user_dao.delete_follow(user_id, unfollow_id)

    def save_profile_picture(self, profile_pic, user_id):
        upload_path = f"{'profile_image/'}{user_id}{'.png'}"
        self.s3.upload_fileobj(
            profile_pic,
            self.config['S3_BUCKET'],
            upload_path
        )

        image_url = f"{self.config['S3_BUCKET_URL']}{upload_path}"

        return self.user_dao.update_profile_picture(image_url, user_id)

    def get_profile_picture(self, user_id):
        return self.user_dao.get_profile_picture(user_id)