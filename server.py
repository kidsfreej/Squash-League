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
divisions = {}
facilities = {}
@app.route("/submitnewteam",methods=["POST"])
def add_new_team():

    t = Team(request.form["fullName"],request.form["shortName"],request.form["division"],Weekdays.parse_weekdays(request.form,"practiceDays"),request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],Weekdays.parse_weekdays(request.form,"noMatchDays"),request.form["homeMatchPCT"], request.form["startDate"])
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    if t.fullName.value in teams:
        return render_template("submitnewteam_fail.html",errors=[t.fullName.value+" is already a team!"])
    teams[t.fullName.value] = t


    return render_template("submitnewteam.html",data=t.properties)
@app.route("/newteam",methods=["GET"])
def newteam_page():
    try:
        return render_template("newteam.html", facilities=facilities,divisions=divisions)
    except Exception as e:
        print(e)
@app.route("/",methods=["GET"])
def index_page():

    return send_from_directory("./websites","index.html")

@app.route("/edit",methods=["POST","GET"])
def edit_page():

    if request.method=="POST":
        if request.form["delete"] not in teams:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Team does not exit!"
        teams.pop(request.form["delete"])

        return render_template("selectteamedit.html", teams=teams)
    arg = request.args.get("team")
    if arg==None:
        return render_template("selectteamedit.html",teams=teams)

    if arg in teams:
        return render_template("editteam.html", team=teams[arg], facilities=facilities,divisions=divisions)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"
@app.route("/submitedit",methods=["POST"])
def submit_edit_page():
    name  = request.form["teamname"]
    if name in teams:

        t = Team(request.form["fullName"], request.form["shortName"], request.form["division"],
                 Weekdays.parse_weekdays(request.form, "practiceDays"), request.form["homeFacility"],
                 request.form["alternativeFacility"], request.form["noPlayDates"],
                 Weekdays.parse_weekdays(request.form, "noMatchDays"), request.form["homeMatchPCT"],
                 request.form["startDate"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        teams.pop(request.form["teamname"])
        teams[t.fullName.value] = t
        return render_template("submiteditteam.html",data=t.properties)

    return "Ok  this should neve everr happen. "
@app.route("/delete",methods=["GET"])
def delete_page():
    name = request.args.get("team")
    if name==None or name not in teams:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a team</h1>"
    db.remove_team(name)
    return render_template("deleteteam.html",name=name)

@app.route("/newdivision")
def new_division():
    return send_from_directory("./websites", "newdivision.html")
@app.route("/submitnewdivision",methods=["POST"])
def submit_new_division():

    t = Division(request.form["year"], request.form["fullName"], request.form["shortName"],
                 request.form["start"], request.form["end"])
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in divisions:
        return render_template("submitnewteam_fail.html", errors=[t.fullName.value + " is already a facility!"])
    divisions[t.fullName.value] = t

    return render_template("submitnewdivision.html", data=t.properties)

@app.route("/editdivision",methods=["GET","POST"])
def edit_division():

    if request.method=="POST":
        if request.form["delete"] not in divisions:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Division does not exit!"
        divisions.pop(request.form["delete"])

        return render_template("selectdivisionedit.html", teams=divisions)
    arg = request.args.get("division")
    if arg==None:
        return render_template("selectdivisionedit.html", teams=divisions)

    if arg in divisions:
        return render_template("editdivision.html", facility=divisions[arg])
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"
@app.route("/submiteditdivision",methods=["POST"])
def submit_edit_division():
    name = request.form["facilityname"]
    if name in divisions:

        t = Division(request.form["year"], request.form["fullName"], request.form["shortName"], request.form["start"], request.form["end"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        divisions.pop(name)
        divisions[t.fullName.value] = t
        # db.remove_team(name)
        # db.add_team(t)
        return render_template("submitteddivision.html", data=t.properties)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(name)} is not a division!!"
@app.route("/deletedivision")
def delete_division():
    name = request.args.get("division")
    if name == None:
        return "fat L"
    if name not in divisions:
        return f"<a href='/'>Home</a><h1>ERROR: {html.escape(name)} is not a division</h1>"
    return render_template("deletedivision.html",name=name)

app.run()