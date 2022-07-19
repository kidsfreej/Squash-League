from flask import Flask
from flask import send_from_directory
from flask import render_template
app = Flask(__name__)

@app.route("/submitnewteam",methods=["POST"])
def add_new_team():
    return render_template("websites/submitnewteam.html",data=)
@app.route("/")
def index():
    return send_from_directory("/websites","index.html")

app.run()