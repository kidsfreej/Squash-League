import time

import flask


from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
import threading

import montecarlo
from database import Database
import pickle
from montecarlo import *
app = Flask(__name__)



with open("data.pickle","rb") as f:
    d = pickle.load(f)
    teams = d["teams"]
    divisions = d["divisions"]
    facilities = d["facilities"]
pickle_data = {"teams": teams, "divisions": divisions, "facilities": facilities}

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
        for team in teams:
            if team.division.value == request.form["delete"]:
                team.division.value = None
        return render_template("selectdivisionedit.html", teams=divisions)
    arg = request.args.get("division")
    if arg==None:
        return render_template("selectdivisionedit.html", teams=divisions)

    if arg in divisions:
        return render_template("editdivision.html", facility=divisions[arg])
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"

@app.route("/deletedivision")
def delete_division():
    name = request.args.get("division")
    if name == None:
        return "fat L"
    if name not in divisions:
        return f"<a href='/'>Home</a><h1>ERROR: {html.escape(name)} is not a division</h1>"
    return render_template("deletedivision.html",name=name)


@app.route("/newfacility")
def new_facility_page():
    return render_template("newfacility.html",teams=teams)

@app.route("/submitnewfacility",methods=["POST"])
def add_new_facility():
    parsed_teams = []
    for i in range(1,31):
        if "team-"+str(i) in request.form:
            if request.form["team-"+str(i)]=="$none" or request.form["team-"+str(i)] in parsed_teams:
                continue
            parsed_teams.append(request.form["team-"+str(i)])
        else:
            break
    t = Facility(request.form["fullName"],request.form["shortName"],Weekdays.parse_weekdays(request.form,"daysCanHost"),request.form["datesCantHost"],parsed_teams)
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    if t.fullName.value in facilities:
        return render_template("submitnewteam_fail.html",errors=[t.fullName.value+" is already a facility!"])
    facilities[t.fullName.value] = t


    return render_template("submitnewfacility.html",data=t.properties)

@app.route("/editfacilities")
def edit_facilities():

    if request.method=="POST":
        if request.form["delete"] not in facilities:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Facility does not exit!"
        facilities.pop(request.form["delete"])
        for team in teams:
            if team.homeFacility.value == request.form["delete"]:
                team.homeFacility.value = None
            if team.alternateFacility.value == request.form["delete"]:
                team.alternateFacility.value = None
        return render_template("selectfacilityedit.html", teams=facilities)
    arg = request.args.get("facility")
    if arg==None:
        return render_template("selectfacilityedit.html",teams=facilities)

    if arg in facilities:
        return render_template("editfacility.html", facility=facilities[arg], teams=teams)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"
@app.route("/submiteditfacility",methods=["POST"])
def submit_edit_facility():
    name = request.form["facilityname"]
    if name in facilities:

        parsed_teams = []
        for i in range(1, 31):
            if "team-" + str(i) in request.form:
                if request.form["team-" + str(i)] == "$none" or request.form["team-" + str(i)] in parsed_teams:
                    continue
                parsed_teams.append(request.form["team-" + str(i)])
            else:
                break
        t = Facility(request.form["fullName"], request.form["shortName"],
                     Weekdays.parse_weekdays(request.form, "daysCanHost"), request.form["datesCantHost"], parsed_teams)

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        facilities.pop(name)
        facilities[t.fullName.value] = t
        # db.remove_team(name)
        # db.add_team(t)
        return  render_template("submiteditfacility.html", data=t.properties)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(name)} is not a facility!!"
@app.route("/submiteditdivision",methods=["POST"])
def submit_edit_division():
    name = request.form["divisionname"]
    if name in divisions:

        t = Division(request.form["year"], request.form["fullName"], request.form["shortName"],
                     request.form["start"], request.form["end"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        divisions.pop(name)
        divisions[t.fullName.value] = t
        # db.remove_team(name)
        # db.add_team(t)
        return render_template("submiteditdivision.html", data=t.properties)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(name)} is not a division!!"

@app.route("/deletefacility")
def delete_facility():
    name = request.args.get("facility")
    if name==None or name not in facilities:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a facility</h1>"
    return render_template("deletefacility.html",name=name)

@app.route("/generateschedule",methods=["POST","GET"])
def generate_schedule_page():
    global isscheduling
    global cap_iterations
    global schedules_dict
    global iterations_counter

    if 'iterations' in request.form:

        cap_iterations = int(request.form["iterations"])*len(teams)
        threading.Thread(target=generate_schedule, args=(request.form["name"],divisions[request.form["division"]], int(request.form["iterations"]), teams, facilities, isscheduling, iterations_counter, schedules_dict)).start()


        return render_template("loadingscreen.html",iters=iterations_counter[0],maxiters=cap_iterations,name=request.form["name"])

    return render_template("generateschedule.html", divisions=divisions)
@app.route("/loadingscreenpost",methods=["POST"])
def loading_screen():
    global isscheduling
    global cap_iterations
    global schedules_dict
    global iterations_counter
    if request.form["name"] in schedules_dict:
        return flask.redirect("/editschedule?schedule="+request.form["name"])
    return render_template("loadingscreen.html", iters=iterations_counter[0], maxiters=cap_iterations,name=request.form["name"])
@app.route("/cancelscheduler",methods=["POST"])
def cancel_scheduler():
    global isscheduling
    isscheduling[0] = False
    return flask.redirect("/")
@app.route("/editschedule",methods=["GET","POST"])
def edit_schedules():
    global schedules_dict

    schedu:Schedule=  schedules_dict[request.args["schedule"]]
    print(schedu)
    print(schedu.games_in_table_order())
    return render_template("scheduledisplay.html",teams=list(schedu.teams.values()),scheduleArr=schedu.games_in_table_order())
def deubg_pickle():
    while True:
        time.sleep(5)
        with open("data.pickle","wb") as f:
            pickle.dump(pickle_data,f)
# @app.route("")
t = threading.Thread(target=deubg_pickle)
t.start()
app.run()
