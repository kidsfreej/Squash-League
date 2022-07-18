from flask import Flask
from flask import send_from_directory
app = Flask(__name__)
@app.route("/submitnewteam")
def add_new_team():

@app.route("/")
def index():
    return send_from_directory("./","index.html")

app.run()