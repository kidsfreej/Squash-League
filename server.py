from TeamData import *
from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
app = Flask(__name__)


teams = []

@app.route("/submitnewteam",methods=["POST"])
def add_new_team():
    t = Team(request.form["fullName"],request.form["shortName"],request.form["division"],request.form["practiceDays"],request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],request.form["noMatchDays"],request.form["homeMatchPCT"], request.form["startDate"])
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    teams.append(t)

    return render_template("submitnewteam.html",data=t.properties)
@app.route("/newteam")
def newteam_page():
    return send_from_directory("./websites","newteam.html")
@app.route("/")
def index_page():
    return send_from_directory("./websites","index.html")
app.run()