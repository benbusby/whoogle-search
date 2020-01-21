from flask import Flask
import os

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)) + '/static')

from app import routes
