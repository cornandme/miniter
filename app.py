from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
import boto3
import botocore

import config
from model import UserDAO, TweetDAO
from service import UserService, TweetService
from view import create_endpoints

class Services:
    pass

def create_app(test_config = None):
    app = Flask(__name__)
    CORS(app)
    
    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)
        
    database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0, echo=True)

    # persistence layer
    user_dao = UserDAO(database)
    tweet_dao = TweetDAO(database)

    # business layer
    s3_client = boto3.client(
        's3',
        aws_access_key_id = app.config['S3_ACCESS_KEY'],
        aws_secret_access_key = app.config['S3_SECRET_KEY']
    )

    services = Services
    services.user_service = UserService(user_dao, app.config, s3_client)
    services.tweet_service = TweetService(tweet_dao)

    create_endpoints(app, services)

    return app