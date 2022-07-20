from TeamData import *
from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
app = Flask(__name__)


teams = {}

@app.route("/submitnewteam",methods=["POST"])
def add_new_team():
    t = Team(request.form["fullName"],request.form["shortName"],request.form["division"],request.form["practiceDays"],request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],request.form["noMatchDays"],request.form["homeMatchPCT"], request.form["startDate"])
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    if t.fullName.value in teams:
        return render_template("submitnewteam_fail.html",errors=[t.fullName.value+" is already a team!"])
    teams[t.fullName.value] = t

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
def editor_page():
    name  = request.form["teamname"]
    if name in teams:

        t= Team(request.form["fullName"],request.form["shortName"],request.form["division"],request.form["practiceDays"],request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],request.form["noMatchDays"],request.form["homeMatchPCT"], request.form["startDate"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        teams.pop(request.form["teamname"])
        teams[t.fullName.value] = t
        return render_template("submiteditteam.html",data=t.properties)
    return "Ok  this should neve everr happen. "
@app.route("/delete")
def delete_page():
    name = request.args.get("team")
    if name==None or name not in teams:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a team</h1>"
    return render_template("deleteteam.html",name=name)


app.run()