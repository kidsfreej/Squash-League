
from __future__ import annotations
import time
import urllib.parse
import flask
from markupsafe import Markup
import os.path
from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
import threading
from scheduler import *
from database import Database
import pickle
import urllib.parse
app = Flask(__name__)
@app.context_processor
def global_vars():
    return dict(urlparse=lambda x:urllib.parse.quote_plus(str(x)))

teams={}
divisions={}
facilities={}
if os.path.exists("data.pickle"):
    with open("data.pickle","rb") as f:
        d = pickle.load(f)
        if "teams" in d:
            teams :Dict[str,Team] = d["teams"]
        if "divisions" in d:
            divisions = d["divisions"]
        if "facilities" in d:
            facilities :Dict[str,Facility]= d["facilities"]
        if "master_schedules" in d:
            MasterSchedule.master_schedules = d["master_schedules"]
def save_pickle():
    pickle_data = {"teams": teams, "divisions": divisions, "facilities": facilities,"master_schedules":MasterSchedule.master_schedules}
    with open("data.pickle","wb") as f:
        pickle.dump(pickle_data,f)
def sched_thread(name,iterations,divisions,teams,facilities,do_update):

    if not do_update:
        master = MasterSchedule(divisions, teams, facilities)
    else:
        master = MasterSchedule.master_schedules[name]

    MasterSchedule.current_schedule= name

    result = master.generate_master_schedule(iterations,do_update)


    if result:
        MasterSchedule.master_schedules[name] = result
    save_pickle()

    MasterSchedule.is_scheduling = False
    MasterSchedule.is_updating = False
def generate_schedule_thread(name,iterations,divisions,teams,facilities,do_update=False):

    MasterSchedule.is_updating=do_update
    MasterSchedule.is_scheduling=not do_update
    MasterSchedule.cap_iterations=iterations
    MasterSchedule.iteration_counter=0
    threading.Thread(target=sched_thread,args=(name,iterations,divisions,teams,facilities,do_update)).start()

def delete_team(old_name):
    for fac_name in facilities:
        if old_name in facilities[fac_name].allowedTeams.value:
            facilities[fac_name].allowedTeams.value.remove(old_name)
    for master_sched in MasterSchedule.master_schedules.values():
        if old_name in master_sched.rawTeams:
            master_sched.rawTeams.pop(old_name)
        for schedule in master_sched.schedules:
            if old_name in schedule.teams:
                schedule.teams.pop(old_name)
            if old_name in schedule.games_by_team:
                schedule.games_by_team.pop(old_name)
            if old_name in schedule.team_home_plays:
                schedule.team_home_plays.pop(old_name)
            if old_name in schedule.team_away_plays:
                schedule.team_away_plays.pop(old_name)

            for date in schedule.games:
                to_remove = []
                for game in schedule.games[date]:
                    if game.rteam1.fullName == old_name or game.rteam2.fullName == old_name:
                        to_remove.append(game)
                for r in to_remove:
                    schedule.games[date].remove(r)
            to_remove = []
            for combo,game in schedule.games_by_combo_gen():
                if old_name in (combo[0].fullName,combo[1].fullName):
                    to_remove.append(combo)
            for r in to_remove:
                schedule.games_by_combo.pop(r)

def delete_facility(old_name):

    for team in teams:
        either = False
        if teams[team].homeFacility.value==old_name:
            teams[team].homeFacility.value=  None
            either = True
        if teams[team].alternateFacility.value==old_name:
            teams[team].alternateFacility.value=  None
            either = True
        if either:
            change_team(team,teams[team])
    for master_sched  in MasterSchedule.master_schedules.values():
        if old_name in master_sched.rawFacilities:
            master_sched.rawFacilities.pop(old_name)
        for schedule in master_sched.schedules:
            if old_name in schedule.facilities:
                schedule.facilities.pop(old_name)


def change_team(old_name,new_team:Team):
    for fac_name in facilities:
        if old_name in facilities[fac_name].allowedTeams.value and old_name != new_team.fullName.value:
            facilities[fac_name].allowedTeams.value.remove(old_name)
            facilities[fac_name].allowedTeams.value.append(new_team.fullName.value)
            change_facility(fac_name,facilities[fac_name])
    newraw= RawTeam(new_team)
    for master_sched in MasterSchedule.master_schedules.values():
        if old_name in master_sched.rawTeams:
            master_sched.rawTeams.pop(old_name)
            master_sched.rawTeams[new_team.fullName.value] = newraw
        for schedule in master_sched.schedules:
            if old_name in schedule.teams:
                schedule.teams.pop(old_name)
                schedule.teams[new_team.fullName.value] = newraw
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

            for date in schedule.games:
                for game in schedule.games[date]:
                    if game.rteam1.fullName == old_name:
                        game.rteam1 = newraw
                    if game.rteam2.fullName == old_name:
                        game.rteam2 = newraw
            to_change = {}
            for combo,game in schedule.games_by_combo_gen():

                if combo[0].fullName == old_name:
                    to_change[(newraw,combo[1])] = (game,combo)
                if combo[1].fullName == old_name:
                    to_change[(combo[0],newraw)] = (game,combo)
                if game is None:
                    continue
                if game.rteam1.fullName == old_name:
                    game.rteam1 = newraw
                if game.rteam2.fullName == old_name:
                    game.rteam2 = newraw
            for k,v in to_change.items():
                schedule.games_by_combo[k]=schedule.games_by_combo.pop(v[1])
def change_facility(old_name,new_facilitiy:Facility):
    if old_name != new_facilitiy.fullName.value:
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
    for master_sched  in MasterSchedule.master_schedules.values():
        if old_name in master_sched.rawFacilities:
            master_sched.rawFacilities.pop(old_name)
            master_sched.rawFacilities[new_facilitiy.fullName.value] =  RawFacility(new_facilitiy)
        for schedule in master_sched.schedules:
            if old_name in schedule.facilities:
                schedule.facilities.pop(old_name)
                schedule.facilities[new_facilitiy.fullName.value] = RawFacility(new_facilitiy)

            for combo,game in schedule.games_by_combo_gen():
                if game is None:
                    continue
                if game.rfacility.fullName == old_name:
                    game.rfacility = RawFacility(new_facilitiy)
            for team in schedule.games_by_team:
                for game in schedule.games_by_team[team]:
                    if game.rfacility.fullName == old_name:
                        game.rfacility = RawFacility(new_facilitiy)
def change_division(old_name,new_division:Division):
    for team in teams:
        if teams[team].division.value == old_name:
            teams[team].division.value= new_division.fullName.value
            change_team(team,teams[team])
    newraw = RawDivision(new_division)
    for master_sched in MasterSchedule.master_schedules.values():
        if old_name in master_sched.rawDivisions:
            master_sched.rawDivisions.pop(old_name)
            master_sched.rawDivisions[new_division.fullName.value]=newraw
        for schedule in master_sched.schedules:
            if schedule.division.fullName == old_name:
                schedule.division =newraw
                for combo, game in schedule.games_by_combo_gen():
                    if game is None:
                        continue
                    game.division_name = new_division.fullName.value
                for team in schedule.games_by_team:
                    for game in schedule.games_by_team[team]:
                        game.division_name = new_division.fullName.value

def generate_csv_facility(facility,master_sched:MasterSchedule):
    games = []

    for schedule in master_sched.schedules:
        for date in schedule.games:
            for game in schedule.games[date]:
                if game.rfacility.fullName==facility:
                    games.append(game)
    games = sorted(games,key=lambda x: x.date)
    return "Date,Team 1,Team 2,Facility\n"+'\n'.join(list(map(lambda x:x.csv_display_versus_with_facility() if x else '',games)))

@app.route("/submitnewteam",methods=["POST"])
def add_new_team():

    t = Team(request.form["fullName"],request.form["shortName"],request.form["division"],Weekdays.parse_weekdays(request.form,"practiceDays"),request.form["homeFacility"],request.form["alternativeFacility"],request.form["noPlayDates"],Weekdays.parse_weekdays(request.form,"noMatchDays"),request.form["homeMatchPCT"], request.form["startDate"])
    if len(t.errors)>0:
        return render_template("submitnewteam_fail.html",errors=t.errors)
    if t.fullName.value in teams:
        return render_template("submitnewteam_fail.html",errors=[t.fullName.value+" is already a team!"])
    teams[t.fullName.value] = t
    save_pickle()

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
        delete_team(request.form["delete"])

        return flask.redirect("/edit")
    arg = request.args.get("team")
    if arg==None:
        return render_template("selectteamedit.html",teams=teams,ordered_teams=sorted(list(teams.keys())))

    if arg in teams:
        return render_template("editteam.html",team=teams[arg], facilities=facilities,divisions=divisions)
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
        change_team(request.form["teamname"],t)
        save_pickle()
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
    save_pickle()
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
        return flask.redirect("/editdivision")
    arg = request.args.get("division")
    if arg==None:
        return render_template("selectdivisionedit.html", teams=divisions,ordered_teams=sorted(list(divisions.keys())))

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
    save_pickle()

    return render_template("submitnewfacility.html",data=t.properties)

@app.route("/editfacilities",methods=["GET","POST"])
def edit_facilities():

    if request.method=="POST":
        if request.form["delete"] not in facilities:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Facility does not exit!"
        facilities.pop(request.form["delete"])
        delete_facility(request.form["delete"])
        return flask.redirect("/editfacilities")
    arg = request.args.get("facility")
    if arg==None:
        return render_template("selectfacilityedit.html",teams=facilities,ordered_teams=sorted(list(facilities.keys())))

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
        save_pickle()
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
        save_pickle()
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
    if MasterSchedule.is_scheduling:
        return flask.redirect("/loadingscreenpost?name=" + urllib.parse.quote_plus(MasterSchedule.current_schedule))
    if MasterSchedule.is_updating:
        return flask.redirect("/loadingscreenupdate?name="+urllib.parse.quote_plus(MasterSchedule.current_schedule))
    if 'iterations' in request.form:

        if request.form["name"] in MasterSchedule.master_schedules:
            return "schedule with name already exists"


        teamsbydiv = {division:{x:teams[x] for x in teams if teams[x].division.value==divisions[division].fullName.value} for division in divisions}
        for division in teamsbydiv:
            if len(teamsbydiv[division])<2:
                return "please add more than 1 teams to the "+html.escape(division)+" division"
        MasterSchedule.cap_iterations = int(request.form["iterations"])
        MasterSchedule.is_scheduling = True
        MasterSchedule.DEBUG_global = True
        print("attempting to spawn thread")
        generate_schedule_thread(request.form["name"],MasterSchedule.cap_iterations,divisions,teams,facilities)

        return render_template("loadingscreen.html",iters=MasterSchedule.iteration_counter,maxiters=MasterSchedule.cap_iterations,name=request.form["name"])

    return render_template("generateschedule.html", divisions=divisions)
@app.route("/loadingscreenpost",methods=["GET"])
def loading_screen():
    if request.args["name"] in MasterSchedule.master_schedules:
        return flask.redirect("/viewschedules?schedule="+urllib.parse.quote_plus(request.args["name"]))
    if MasterSchedule.is_scheduling:
        return render_template("loadingscreen.html", iters=MasterSchedule.iteration_counter, maxiters=MasterSchedule.cap_iterations,name=request.args["name"])
    print("wow nothing:",MasterSchedule.DEBUG_global)
    return flask.redirect("/")
@app.route("/cancelscheduler",methods=["POST"])
def cancel_scheduler():
    MasterSchedule.is_scheduling = False
    return flask.redirect("/")
@app.route("/viewschedules",methods=["GET","POST"])
def view_schedules():
    if "schedule" in request.args:
        schedu:MasterSchedule=  MasterSchedule.master_schedules[request.args["schedule"]]
        return render_template("scheduledisplay.html",teamsByDivs={division:[x for x in schedu.rawTeams if schedu.rawTeams[x].division==schedu.rawDivisions[division].fullName] for division in schedu.rawDivisions},divisions=divisions,scheduleArr=list(map(Schedule.games_in_table_order,schedu.schedules)),name=request.args["schedule"],enum=enumerate)
    return render_template("viewschedules.html",schedules=MasterSchedule.master_schedules)


@app.route("/downloadschedule")
def download_schedule():
    if "schedule" in request.args and "division" in request.args:
        try:
            schedu:Schedule=  next(x for x in MasterSchedule.master_schedules[request.args["schedule"]].schedules if x.division.fullName==request.args["division"])
        except:
            return "Invalid url"
        data = schedu.as_csv()
        return flask.Response(data,
                       mimetype="text/plain",
                       headers={"Content-Disposition":
                                    f"attachment;filename={request.args['division']}.csv"})
    if "facility" in request.args and "schedule" in request.args:
        try:
            if  request.args["facility"] not in facilities:
                return "Unknown facility"
            data  = generate_csv_facility(request.args["facility"],MasterSchedule.master_schedules[request.args["schedule"]])
            return flask.Response(data,
                                  mimetype="text/plain",
                                  headers={"Content-Disposition":
                                               f"attachment;filename={request.args['facility']}.csv"})
        except:
            return "Invalid url"
    if "schedule" in request.args:
        print("ok so we do be doin")
        master_sched = MasterSchedule.master_schedules[request.args["schedule"]]
        final_csv = master_sched.generate_csv()
        return flask.Response(final_csv,
                              mimetype="text/plain",
                              headers={"Content-Disposition":
                                           f"attachment;filename={request.args['schedule']}.csv"})
    return "No schedule submitted in GET request"
@app.route("/downloadbyfacility")
def download_by_facility():
    if 'schedule' not in request.args:
        return "no schedule when trying to download by faciltiy"
    if request.args["schedule"] not in MasterSchedule.master_schedules:
        return "Unkown schedule: "+html.escape(request.args["schedule"])
    return render_template("downloadbyfacility.html",facilities=facilities,scheduleName=request.args["schedule"])
@app.route("/editschedule")
def edit_schedules():
    if "team" in request.args:
        if request.args["schedule"] not in schedules_dict:
            return "Unknown schedule"
        if request.args["team"] not in teams:
            return "Unknown team"

    else:
        if request.args["schedule"] not in schedules_dict:
            return "Unknown schedule"

        sched:Schedule = schedules_dict[request.args["schedule"]]

        teamsindiv = {x:teams[x] for x in teams if teams[x].division.value==sched.division.fullName}
        return render_template("editschedule.html",teams=teamsindiv,schedname=request.args["schedule"])


@app.route("/deleteschedule",methods=["GET","POST"])
def delete_schedule():
    if request.method=='POST':
        if request.form["name"] in MasterSchedule.master_schedules:
            MasterSchedule.master_schedules.pop(request.form["name"])
            return flask.redirect("/viewschedules")
        return "bruuuh error related to delete schedule"
    if "schedule" in request.args:
        if request.args["schedule"] not in MasterSchedule.master_schedules:
            return "Unknown Schedule"
        return render_template("deleteschedule.html",name=request.args["schedule"])
    return "No schedule inputted"
@app.route("/updateschedule",methods=["GET","POST"])
def update_schedule_page():
    if request.method=="GET":
        if "schedule" not in request.args:
            return "Please select a schedule to update"
        if request.args["schedule"] not in MasterSchedule.master_schedules:
            return "Non-existant schedule"
        return render_template("updateschedule.html",name=request.args["schedule"])
    if MasterSchedule.is_scheduling:
        return flask.redirect("/loadingscreenpost?name=" + urllib.parse.quote_plus(MasterSchedule.current_schedule))
    if MasterSchedule.is_updating:
        return flask.redirect("/loadingscreenupdate?name="+urllib.parse.quote_plus(MasterSchedule.current_schedule))
    MasterSchedule.cap_iterations=int(request.form["iterations"])
    print("attempting to spawn thread")

    generate_schedule_thread(request.form["name"], MasterSchedule.cap_iterations, divisions, teams, facilities,True)
    return flask.redirect("/loadingscreenupdate?name="+urllib.parse.quote_plus(request.form["name"]))
@app.route("/loadingscreenupdate")
def loading_screen_update():
    if not MasterSchedule.is_updating:
        return flask.redirect("/viewschedules?schedule=" + urllib.parse.quote_plus(request.args["name"]))
    return render_template("loadingscreenupdate.html", iters=MasterSchedule.iteration_counter,maxiters=MasterSchedule.cap_iterations, name=request.args["name"])
@app.route("/cancelupdater",methods=["POST"])
def cancel_updater():
    MasterSchedule.is_updating=False

    return flask.redirect("/")

@app.route("/leaguesettings",methods=["POST","GET"])
def league_settings():
    if request.method=="GET":
        return render_template("leaguesettings.html",noPlayDates=Schedule.str_league_wide_no_play_dates)
    parsed = Dates("League Wide No Play Dates",request.form["noPlayDates"])
    if parsed.error:
        return render_template("submitnewteam_fail.html",errors=[error_messages(parsed)])
    Schedule.str_league_wide_no_play_dates= parsed.__repr__()
    Schedule.league_wide_no_play_dates = parsed.to_set()
    return render_template("leaguesettingssuccess.html",noPlayDates=Schedule.str_league_wide_no_play_dates)

# for i in range(2):
#     add_team = []
#     add_divisions= []
#     for team in teams.values():
#         randname = "clone"
#         for fac in facilities.values():
#             if team.fullName.value in fac.allowedTeams.value:
#                 fac.allowedTeams.value.append(team.fullName.value +randname)
#         add_team.append(Team(team.fullName.value +randname,team.shortName.value+randname,team.division.value+" clone",team.practiceDays.days,team.homeFacility.value,team.alternateFacility.value,team.noPlayDates.__repr__(),team.noMatchDays.days,team.homeMatchPCT.value,team.startDate.__repr__()))
#     for t in add_team:
#         teams[t.fullName.value] = t
#     for division in divisions.values():
#         add_divisions.append(Division(division.year.value,division.fullName.value +" clone",division.shortName.value,division.start.__repr__(),division.end.__repr__()))
#     for t in add_divisions:
#         divisions[t.fullName.value] = t

ON_HEROKU = os.environ.get('PORT')



if __name__ == '__main__':
    print("cool epic on heroku")

    port = int(os.environ.get('PORT', 8000))  # as per OP comments default is 17995

    app.run(port=port)
#TODO:
# 1: whole league, all matches, all divisions
# 2: by division
# 3: by facility
# things that could change:
# practice days

