from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
    
    @staticmethod
    def verify(username, password):
        if username == Config.DEFAULT_USERNAME and password == Config.DEFAULT_PASSWORD:
            return User(username)
        return None
    
    @staticmethod
    def get(user_id):
        if user_id == Config.DEFAULT_USERNAME:
            return User(user_id)
        return None
