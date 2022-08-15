
from __future__ import annotations
import time
import urllib.parse
import flask
from markupsafe import Markup

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
    teams :Dict[str,Team] = d["teams"]
    divisions = d["divisions"]
    facilities :Dict[str,Facility]= d["facilities"]
pickle_data = {"teams": teams, "divisions": divisions, "facilities": facilities}
def change_team(old_name,new_team:Team):
    for fac_name in facilities:
        if old_name in facilities[fac_name].allowedTeams.value and old_name != new_team.fullName.value:
            facilities[fac_name].allowedTeams.value.remove(old_name)
            facilities[fac_name].allowedTeams.value.append(new_team.fullName.value)
            ch
    for sched in schedules_dict:
        schedule = schedules_dict[sched]
        if old_name in schedule.teams:
            schedule.teams.pop(old_name)
            schedule.teams[new_team.fullName.value] = RawTeam(new_team)
        if old_name in schedule.games_by_team:
            schedule.games_by_team[new_team.fullName.value] = schedule.games_by_team.pop(old_name)
            for game in schedule.games_by_team[new_team.fullName.value]:
                if game.rteam1.fullName == old_name:
                    game.rteam1=schedule.teams[new_team.fullName.value]
                if game.rteam2.fullName == old_name:
                    game.rteam2 = schedule.teams[new_team.fullName.value]
        if old_name in schedule.team_home_plays:
            schedule.team_home_plays[new_team.fullName.value]=schedule.team_home_plays.pop(old_name)
        if old_name in schedule.team_away_plays:
            schedule.team_away_plays[new_team.fullName.value]=schedule.team_away_plays.pop(old_name)
def change_facility(old_name,new_facilitiy:Facility):
    for team in teams:
        either = False
        if teams[team].homeFacility.value==old_name:
            teams[team].homeFacility.value=  new_facilitiy.fullName.value
            either = True
        if teams[team].alternateFacility.value==old_name:
            teams[team].alternateFacility.value=  new_facilitiy.fullName.value
            either = True
        if either:
            change_team(team,teams[team])
    for sched in schedules_dict:
        schedule = schedules_dict[sched]
        if old_name in schedule.facilities:
            schedule.facilities.pop(old_name)
            schedule.facilities[new_facilitiy.fullName.value] = RawFacility(new_facilitiy)
        for date in schedule.games:
            for game in schedule.games[date]:
                if game.rfacility.fullName == old_name:
                    game.rfacility.fullName = new_facilitiy.fullName.value

def change_division(old_name,new_division:Division):
    for team in teams:
        if teams[team].division.value == old_name:
            teams[team].division.value= new_division.fullName.value
            change_team(team,teams[team])
    for sched in schedules_dict:
        schedule : Schedule = schedules_dict[sched]
        if schedule.division.fullName == old_name:
            schedule.division = RawDivision(new_division)
@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote_plus(s)
    return Markup(s)
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
        for facility in facilities:
            for i in range(len(facilities[facility].allowedTeams)):
                if facilities[facility].allowedTeams.value[i]==name:
                    facilities[facility].allowedTeams.value[i] = request.form["fullName"]
        teams.pop(request.form["teamname"])
        teams[t.fullName.value] = t
        change_team(request.form["teamname"],t)

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
            if teams[team].division.value == request.form["delete"]:
                teams[team].division.value = None
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

@app.route("/editfacilities",methods=["GET","POST"])
def edit_facilities():

    if request.method=="POST":
        if request.form["delete"] not in facilities:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Facility does not exit!"
        facilities.pop(request.form["delete"])
        for team in teams:
            if teams[team].homeFacility.value == request.form["delete"]:
                teams[team].homeFacility.value = None
            if teams[team].alternateFacility.value == request.form["delete"]:
                teams[team].alternateFacility.value = None
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
        change_facility(name,t)
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

        change_division(name,t)
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
    global  schedules_dict
    global iterations_counter

    if 'iterations' in request.form:
        teamsindiv = {x:teams[x] for x in teams if teams[x].division.value==request.form["division"]}
        if len(teamsindiv)<2:
            return "please add more than 1 teams to the division"
        cap_iterations = int(request.form["iterations"])
        threading.Thread(target=generate_schedule, args=(request.form["name"],divisions[request.form["division"]], int(request.form["iterations"]), teamsindiv, facilities, isscheduling, iterations_counter, schedules_dict)).start()


        return render_template("loadingscreen.html",iters=iterations_counter[0],maxiters=cap_iterations,name=request.form["name"])

    return render_template("generateschedule.html", divisions=divisions)
@app.route("/loadingscreenpost",methods=["POST"])
def loading_screen():
    global isscheduling
    global cap_iterations
    global schedules_dict
    global iterations_counter
    if request.form["name"] in schedules_dict:
        print(request.form["name"])
        print(request.form["name"])
        print(request.form["name"])
        return flask.redirect("/viewschedules?schedule="+(request.form["name"]))
    return render_template("loadingscreen.html", iters=iterations_counter[0], maxiters=cap_iterations,name=request.form["name"])
@app.route("/cancelscheduler",methods=["POST"])
def cancel_scheduler():
    global isscheduling
    isscheduling[0] = False
    return flask.redirect("/")
@app.route("/viewschedules",methods=["GET","POST"])
def view_schedules():
    global schedules_dict
    if "schedule" in request.args:
        schedu:Schedule=  schedules_dict[request.args["schedule"]]
        return render_template("scheduledisplay.html",teams=list(schedu.teams.values()),scheduleArr=schedu.games_in_table_order(),name=request.args["schedule"])
    return render_template("viewschedules.html",schedules=schedules_dict)


@app.route("/downloadschedule")
def download_schedule():
    if "schedule" in request.args:
        try:
            schedu:Schedule=  schedules_dict[request.args["schedule"].split(".")[0]]
        except:
            return "Invalid url"
        data = schedu.as_csv()
        return flask.Response(data,
                       mimetype="text/plain",
                       headers={"Content-Disposition":
                                    f"attachment;filename={request.args['schedule']}"})

    return "No schedule"
@app.route("/downloadbyfacility")
def download_by_facility():
    global schedules_dict
    facility_arr = []
    for sched in schedules_dict:
        facility_arr+=list(schedules_dict[sched].facilities.keys())

def debug_pickle():
    while True:
        time.sleep(5)
        with open("data.pickle","wb") as f:
            pickle.dump(pickle_data,f)
t = threading.Thread(target=debug_pickle)
t.start()
app.run(port=8080)
#TODO:
# 1: whole league, all matches, all divisions
# 2: by division
# 3: by facility
# things that could change:
# practice days
