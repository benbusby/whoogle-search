from cryptography.fernet import Fernet
from flask import Flask
import os

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)) + '/static')
app.secret_key = Fernet.generate_key()

from app import routes
