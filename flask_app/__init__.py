from flask import Flask

from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = "where do you want to eat"

load_dotenv()