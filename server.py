from TeamData import *
from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
from database import Database

app = Flask(__name__)

db = Database()
db.print_all()


teams = db.get_teams()
#DEBUG
teams = {}
facilities = {}
@app.route("/submitnewteam",methods=["POST"])
def add_new_team():

    t = Team(request.form["fullName"],request.form["shortName"],request.form["division"],Weekdays.parse_weekdays(request.form,"practiceDays"),request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],Weekdays.parse_weekdays(request.form,"noMatchDays"),request.form["homeMatchPCT"], request.form["startDate"])
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    if t.fullName.value in teams:
        return render_template("submitnewteam_fail.html",errors=[t.fullName.value+" is already a team!"])
    teams[t.fullName.value] = t
    db.add_team(t)

    return render_template("submitnewteam.html",data=t.properties)
@app.route("/newteam")
def newteam_page():
    return send_from_directory("./websites","newteam.html")
@app.route("/")
def index_page():

    return send_from_directory("./websites","index.html")

@app.route("/edit",methods=["POST","GET"])
def edit_page():
    if request.method=="POST":
        teams.pop(request.form["delete"])
        return render_template("selectteamedit.html", teams=teams)
    arg = request.args.get("team")
    if arg==None:
        return render_template("selectteamedit.html",teams=teams)

    if arg in teams:
        return render_template("editteam.html",team=teams[arg])
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"
@app.route("/submitedit",methods=["POST"])
def submit_edit_page():
    name  = request.form["teamname"]
    if name in teams:

        t= Team(request.form["fullName"],request.form["shortName"],request.form["division"],request.form["practiceDays"],request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],request.form["noMatchDays"],request.form["homeMatchPCT"], request.form["startDate"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        teams.pop(request.form["teamname"])
        teams[t.fullName.value] = t
        db.remove_team(name)
        db.add_team(t)
        return render_template("submiteditteam.html",data=t.properties)
    return "Ok  this should neve everr happen. "
@app.route("/delete")
def delete_page():
    name = request.args.get("team")
    if name==None or name not in teams:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a team</h1>"
    db.remove_team(name)
    return render_template("deleteteam.html",name=name)

@app.route("/newfacility")
def new_facility():
    return send_from_directory("./websites", "newfacility.html")
@app.route("/submitnewfacility",methods=["POST"])
def submit_new_facility():

    t = Facility(request.form["year"], request.form["fullName"], request.form["shortName"],
             request.form["start"], request.form["end"])
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in facilities:
        return render_template("submitnewteam_fail.html", errors=[t.fullName.value + " is already a facility!"])
    facilities[t.fullName.value] = t

    return render_template("submitnewfacility.html", data=t.properties)

@app.route("/editfacility",methods=["GET","POST"])
def edit_facility():
    if request.method=="POST":
        if request.form["delete"] not in facilities:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Facility does not exit!"
        facilities.pop(request.form["delete"])
        return render_template("selectteamedit.html", teams=teams)
    arg = request.args.get("facility")
    if arg==None:
        return render_template("selectteamedit.html",teams=facilities)

    if arg in facilities:
        return render_template("editfacility.html",facility=facilities[arg])
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"
@app.route("/submiteditfacility")
def submit_edit_facility():
    name = request.form["facilityname"]
    if name in teams:

        t = Facility(request.form["year"],request.form["fullName"],request.form["shortName"],request.form["start"],request.form["end"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        facilities.pop(name)
        facilities[t.fullName.value] = t
        # db.remove_team(name)
        # db.add_team(t)
        return render_template("submiteditteam.html", data=t.properties)
    return "Ok  this should neve everr happen. "
@app.route("/deletefacility")
def delete_facility():
    name = request.args.get("facility")
    if name==None or name not in facilities:
        return f"<a href='/'>Home</a><h1>ERROR: {html.escape(name)} is not a facility</h1>"
    # db.remove_team(name)
    return render_template("deletefacility.html",name=name)

app.run()