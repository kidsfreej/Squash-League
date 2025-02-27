from __future__ import annotations

import urllib.parse
import flask


from flask import Flask
from flask import send_from_directory
from flask import render_template
from flask import request
import threading
from scheduler import *
import pickle
import urllib.parse
from flask_htpasswd import HtPasswdAuth
import redis
from settings import *
import zlib
app = Flask(__name__)
app.config['FLASK_HTPASSWD_PATH'] = 'password.txt'
app.config['FLASK_SECRET'] = 'suepr secret stirng of text dont share this with anyone '
htpasswd = HtPasswdAuth(app)
def connect_redis(url=None,port=None,password=None,username=None):
    if url is None:
        r = redis.Redis(host=redis_url,port=redis_port)
        if not r.auth(redis_password,redis_username):
            raise Exception("auth fail")
        return r
    r = redis.Redis(host=url, port=port)
    if not r.auth(password, username):
        raise Exception("auth fail")
    return r
@app.context_processor
def global_vars():
    return dict(urlparse=lambda x: urllib.parse.quote_plus(str(x)))
def load_league_notes(r=None):
    if r is None:
        r= connect_redis()
    v=r.get("league_notes")
    if v:
        return zlib.decompress(v).decode()
    return ""
def save_league_notes(notes,r=None):
    if r is None:
        r = connect_redis()
    r.set("league_notes",zlib.compress(notes.encode(),1))
def load_no_play():
    r = connect_redis()
    no_play=  set()
    no_str = ""

    t = r.get("noplaydates_str")
    if t:
        no_str = t.decode()

    return Dates("",no_str).to_set(),no_str
def save_no_play(league_wide_no_play_dates,str_league_wide_no_play_dates):
    r = connect_redis()
    r.set("noplaydates",pickle.dumps(league_wide_no_play_dates))
    r.set("noplaydates_str", str_league_wide_no_play_dates)
def load_pickle()->tuple[Dict[str,Team],Dict[str,Division],Dict[str,Facility],Dict[str,MasterSchedule],redis.Redis]:
    r = connect_redis()
    teams = {}
    divisions = {}
    facilities = {}
    master_schedules = {}

    if r.exists("teams"):
        for x in r.lrange("teams",0,r.llen("teams")-1):
            temp:Team = pickle.loads(zlib.decompress(x))
            teams[temp.fullName.value] = temp

    if r.exists("divisions"):
        for x in r.lrange("divisions",0,r.llen("divisions")-1):
            temp:Division = pickle.loads(zlib.decompress(x))
            divisions[temp.fullName.value] = temp

    if r.exists("facilities"):
        for x in r.lrange("facilities",0,r.llen("facilities")-1):
            temp:Facility = pickle.loads(zlib.decompress(x))
            facilities[temp.fullName.value] = temp
    if r.exists("master_schedules"):
        for x in r.lrange("master_schedules",0,r.llen("master_schedules")-1):
            temp:MasterSchedule = pickle.loads(zlib.decompress(x))
            master_schedules[temp.name] = temp
    return teams,divisions,facilities,master_schedules,r
def load_master_schedules(r=None):
    master_schedules = {}
    if r is None:
        r = connect_redis()
    if r.exists("master_schedules"):
        for x in r.lrange("master_schedules",0,r.llen("master_schedules")-1):
            temp:MasterSchedule = pickle.loads(zlib.decompress(x))
            master_schedules[temp.name] = temp
    return master_schedules,r
def load_divisions(r=None):
    divisions = {}
    if r is None:
        r= connect_redis()
    if r.exists("divisions"):
        for x in r.lrange("divisions",0,r.llen("divisions")-1):
            temp:Division = pickle.loads(zlib.decompress(x))
            divisions[temp.fullName.value] = temp


    return divisions,r
def load_facilities(r= None):
    facilities = {}
    if r is None:
        r = connect_redis()
    if r.exists("facilities"):
        for x in r.lrange("facilities",0,r.llen("facilities")-1):
            temp:Facility = pickle.loads(zlib.decompress(x))
            facilities[temp.fullName.value] = temp
    return facilities,r
def load_teams(r=None):
    teams = {}
    if r is None:
        r = connect_redis()
    if r.exists("teams"):
        for x in r.lrange("teams",0,r.llen("teams")-1):
            temp:Team = pickle.loads(zlib.decompress(x))
            teams[temp.fullName.value] = temp
    return teams,r
def load_pickle_no_compression(r)->tuple[Dict[str,Team],Dict[str,Division],Dict[str,Facility],Dict[str,MasterSchedule],redis.Redis]:

    teams = {}
    divisions = {}
    facilities = {}
    master_schedules = {}

    if r.exists("teams"):
        for i in range(r.llen("teams")):
            temp:Team = pickle.loads((r.lindex("teams",i)))
            teams[temp.fullName.value] = temp

    if r.exists("divisions"):
        for i in range(r.llen("divisions")):
            temp:Division = pickle.loads((r.lindex("divisions",i)))
            divisions[temp.fullName.value] = temp

    if r.exists("facilities"):
        for i in range(r.llen("facilities")):
            temp:Facility = pickle.loads((r.lindex("facilities",i)))
            facilities[temp.fullName.value] = temp
    if r.exists("master_schedules"):
        for i in range(r.llen("master_schedules")):
            temp:MasterSchedule = pickle.loads((r.lindex("master_schedules",i)))
            master_schedules[temp.name] = temp
    return teams,divisions,facilities,master_schedules,r

def add_pickle(r,team=None,division=None,facility=None,master_schedule=None):
    if team is not None:
        r.lpush("teams",zlib.compress(pickle.dumps(team)))
    if division is not None:
        r.lpush("divisions",zlib.compress(pickle.dumps(division)))
    if facility is not None:
        r.lpush("facilities",zlib.compress(pickle.dumps(facility)))
    if master_schedule is not None:
        r.lpush("master_schedules",zlib.compress(pickle.dumps(master_schedule)))

def delete_pickle(r,team=None,division=None,facility=None,master_schedule=None):
    if team is not None:
        for i in range(r.llen("teams")):
            if pickle.loads(zlib.decompress(r.lindex("teams",i))).fullName.value == team:
                r.lset("teams",i,"$REMOVEME")
                break
    if division is not None:
        for i in range(r.llen("divisions")):
            if pickle.loads(zlib.decompress(r.lindex("divisions", i))).fullName.value == division:
                r.lset("divisions", i, "$REMOVEME")
                break
    if facility is not None:
        for i in range(r.llen("facilities")):
            if pickle.loads(zlib.decompress(r.lindex("facilities", i))).fullName.value == facility:
                r.lset("facilities", i, "$REMOVEME")
                break

    if master_schedule is not None:
        for i in range(r.llen("master_schedules")):
            if pickle.loads(zlib.decompress(r.lindex("master_schedules", i))).name == master_schedule:
                r.lset("master_schedules", i, "$REMOVEME")
                break
    r.lrem("teams",0,"$REMOVEME")
    r.lrem("divisions",0,"$REMOVEME")
    r.lrem("facilities",0,"$REMOVEME")
    r.lrem("master_schedules",0,"$REMOVEME")

def sched_thread(name, iterations, do_update):
    teams, divisions, facilities, master_schedules, redis = load_pickle()

    if not do_update:
        master = MasterSchedule(divisions, teams, facilities,name)
    else:

        master:MasterSchedule = master_schedules[name]
        for t in master.rawTeams:
            print(master.rawTeams[t].noPlayDates)
    no_plays = load_no_play()[0]
    Schedule.league_wide_no_play_dates = no_plays
    save_scheduling_data(current_schedule=name)
    result = master.generate_master_schedule(iterations, do_update)

    if result:
        result.name = name
        delete_pickle(redis,master_schedule=name)
        add_pickle(redis,master_schedule=result)

    is_scheduling = False
    is_updating = False
    save_scheduling_data(is_scheduling, is_updating)


def generate_schedule_thread(name, iterations, do_update=False):

    is_updating = do_update
    is_scheduling = not do_update
    cap_iterations = iterations
    iteration_counter = 0
    save_scheduling_data(is_scheduling,is_updating,iteration_counter,None,cap_iterations)
    threading.Thread(target=sched_thread, args=(name, iterations, do_update)).start()


def delete_team(old_name,teams, divisions, facilities, master_schedules,red):
    facilities_to_change = {}
    scheds_to_change = {}
    for fac_name in facilities:
        if old_name in facilities[fac_name].allowedTeams.value:
            facilities[fac_name].allowedTeams.value.remove(old_name)
            facilities_to_change[fac_name] = facilities[fac_name]
    for master_sched in master_schedules.values():
        if old_name in master_sched.rawTeams:
            master_sched.rawTeams.pop(old_name)
            scheds_to_change[master_sched.name] = master_sched
        for schedule in master_sched.schedules:
            if old_name in schedule.teams:
                schedule.teams.pop(old_name)
                scheds_to_change[master_sched.name] = master_sched
            if old_name in schedule.games_by_team:
                schedule.games_by_team.pop(old_name)
                scheds_to_change[master_sched.name] = master_sched
            if old_name in schedule.team_home_plays:
                schedule.team_home_plays.pop(old_name)
                scheds_to_change[master_sched.name] = master_sched
            if old_name in schedule.team_away_plays:
                schedule.team_away_plays.pop(old_name)
                scheds_to_change[master_sched.name] = master_sched

            for date in schedule.games:
                to_remove = []
                for game in schedule.games[date]:
                    if game.rteam1.fullName == old_name or game.rteam2.fullName == old_name:
                        to_remove.append(game)
                        scheds_to_change[master_sched.name] = master_sched
                for r in to_remove:
                    schedule.games[date].remove(r)
            to_remove = []
            for combo, game in schedule.games_by_combo_gen():
                if old_name in (combo[0].fullName, combo[1].fullName):
                    to_remove.append(combo)
                    scheds_to_change[master_sched.name] = master_sched
            for r in to_remove:
                schedule.games_by_combo.pop(r)
                scheds_to_change[master_sched.name] = master_sched
    edit_pickle(red,facilities=facilities_to_change)

def delete_facility(old_name,teams, divisions, facilities, master_schedules,red):
    facilities.pop(old_name)
    for team in teams:
        either = False
        if teams[team].homeFacility.value == old_name:
            teams[team].homeFacility.value = None
            either = True
        if teams[team].alternateFacility.value == old_name:
            teams[team].alternateFacility.value = None
            either = True
        if either:
            change_team(team, teams[team],teams, divisions, facilities, master_schedules,red)
    changed_masters = {}
    for master_sched in master_schedules.values():
        if old_name in master_sched.rawFacilities:
            master_sched.rawFacilities.pop(old_name)
            changed_masters[master_sched.name] = master_sched
        for schedule in master_sched.schedules:
            if old_name in schedule.facilities:
                schedule.facilities.pop(old_name)
                changed_masters[master_sched.name] = master_sched
            to_remove_games = []
            for date in schedule.games:
                for game in schedule.games[date]:
                   if game.rfacility.fullName == old_name:
                        to_remove_games.append(game)
            for game in to_remove_games:
                schedule.erase_game(game)
    edit_pickle(red,master_schedules=changed_masters)
def edit_pickle(r:redis.Redis,teams:Dict[str,Team]=None, divisions=None, facilities=None, master_schedules=None):
    if teams is not None and len(teams)!=0:
        for i in range(r.llen("teams")):
            temp: Team = pickle.loads(zlib.decompress(r.lindex("teams", i)))
            if temp.fullName.value in teams:
                r.lset("teams",i,zlib.compress(pickle.dumps(teams[temp.fullName.value])))
    if divisions is not None and len(divisions)!=0:
        for i in range(r.llen("divisions")):
            temp: Division = pickle.loads(zlib.decompress(r.lindex("divisions", i)))
            if temp.fullName.value in divisions:
                r.lset("divisions",i,zlib.compress(pickle.dumps(divisions[temp.fullName.value])))
    if facilities is not None and len(facilities)!=0:
        for i in range(r.llen("facilities")):
            temp: Facility = pickle.loads(zlib.decompress(r.lindex("facilities", i)))
            if temp.fullName.value in facilities:
                r.lset("facilities",i,zlib.compress(pickle.dumps(facilities[temp.fullName.value])))
    if master_schedules is not None and len(master_schedules)!=0:
        for i in range(r.llen("master_schedules")):
            temp: MasterSchedule = pickle.loads(zlib.decompress(r.lindex("master_schedules", i)))
            if temp.name in master_schedules:
                r.lset("master_schedules",i,zlib.compress(pickle.dumps(master_schedules[temp.name])))
def change_team(old_name, new_team: Team,teams, divisions, facilities, master_schedules,r:redis.Redis):


    facilities_to_change = {}
    schedules_to_change = {}
    for fac_name in facilities:
        if old_name in facilities[fac_name].allowedTeams.value and old_name != new_team.fullName.value:
            facilities[fac_name].allowedTeams.value.remove(old_name)
            facilities[fac_name].allowedTeams.value.append(new_team.fullName.value)
            facilities_to_change[fac_name] = facilities[fac_name]
            change_facility(fac_name, facilities[fac_name],teams, divisions, facilities, master_schedules,r)
    newraw = RawTeam(new_team)
    for master_sched in master_schedules.values():
        if old_name in master_sched.rawTeams:
            master_sched.rawTeams.pop(old_name)

            master_sched.rawTeams[new_team.fullName.value] = newraw
            schedules_to_change[master_sched.name] = master_sched
        for schedule in master_sched.schedules:
            if old_name in schedule.teams:
                schedule.teams.pop(old_name)
                schedule.teams[new_team.fullName.value] = newraw
                schedules_to_change[master_sched.name] = master_sched
            if old_name in schedule.games_by_team:
                schedule.games_by_team[new_team.fullName.value] = schedule.games_by_team.pop(old_name)
                for game in schedule.games_by_team[new_team.fullName.value]:
                    if game.rteam1.fullName == old_name:
                        game.rteam1 = schedule.teams[new_team.fullName.value]
                        schedules_to_change[master_sched.name] = master_sched
                    if game.rteam2.fullName == old_name:
                        game.rteam2 = schedule.teams[new_team.fullName.value]
                        schedules_to_change[master_sched.name] = master_sched
            if old_name in schedule.team_home_plays:
                schedule.team_home_plays[new_team.fullName.value] = schedule.team_home_plays.pop(old_name)
                schedules_to_change[master_sched.name] = master_sched
            if old_name in schedule.team_away_plays:
                schedule.team_away_plays[new_team.fullName.value] = schedule.team_away_plays.pop(old_name)
                schedules_to_change[master_sched.name] = master_sched

            for date in schedule.games:
                for game in schedule.games[date]:
                    if game.rteam1.fullName == old_name:
                        game.rteam1 = newraw
                        schedules_to_change[master_sched.name] = master_sched
                    if game.rteam2.fullName == old_name:
                        game.rteam2 = newraw
                        schedules_to_change[master_sched.name] = master_sched
            to_change = {}
            for combo, game in schedule.games_by_combo_gen():

                if combo[0].fullName == old_name:
                    to_change[(newraw, combo[1])] = (game, combo)
                if combo[1].fullName == old_name:
                    to_change[(combo[0], newraw)] = (game, combo)
                if game is None:
                    continue
                if game.rteam1.fullName == old_name:
                    game.rteam1 = newraw
                if game.rteam2.fullName == old_name:
                    game.rteam2 = newraw
            for k, v in to_change.items():
                schedule.games_by_combo[k] = schedule.games_by_combo.pop(v[1])
    edit_pickle(r,None,None,facilities_to_change,schedules_to_change)

def change_facility(old_name, new_facilitiy: Facility,teams, divisions, facilities, master_schedules, r):
    teams_to_change = {}
    schedules_to_change = {}
    if old_name != new_facilitiy.fullName.value:
        for team in teams:
            either = False
            if teams[team].homeFacility.value == old_name:
                teams[team].homeFacility.value = new_facilitiy.fullName.value
                either = True
            if teams[team].alternateFacility.value == old_name:
                teams[team].alternateFacility.value = new_facilitiy.fullName.value
                either = True
            if either:
                teams_to_change[team] = teams[team]
                change_team(team, teams[team],teams, divisions, facilities, master_schedules,r)
    for master_sched in master_schedules.values():
        if old_name in master_sched.rawFacilities:
            master_sched.rawFacilities.pop(old_name)
            master_sched.rawFacilities[new_facilitiy.fullName.value] = RawFacility(new_facilitiy)
            schedules_to_change[master_sched.name] = master_sched
            for schedule in master_sched.schedules:
                if old_name in schedule.facilities:
                    schedule.facilities.pop(old_name)
                    schedule.facilities[new_facilitiy.fullName.value] = RawFacility(new_facilitiy)

                for combo, game in schedule.games_by_combo_gen():
                    if game is None:
                        continue
                    if game.rfacility.fullName == old_name:
                        game.rfacility = RawFacility(new_facilitiy)
                for team in schedule.games_by_team:
                    for game in schedule.games_by_team[team]:
                        if game.rfacility.fullName == old_name:
                            game.rfacility = RawFacility(new_facilitiy)
                for date in schedule.games:
                    for game in schedule.games[date]:
                        if game.rfacility.fullName==old_name:
                            game.rfacility=RawFacility(new_facilitiy)

    edit_pickle(r,teams=teams_to_change,master_schedules=schedules_to_change)
def change_division(old_name, new_division: Division,teams, divisions, facilities, master_schedules, r):
    teams_to_change ={}
    schedules_to_change = {}
    for team in teams:
        if teams[team].division.value == old_name:
            teams[team].division.value = new_division.fullName.value
            teams_to_change[team] = teams[team]
            change_team(team, teams[team],teams, divisions, facilities, master_schedules,r)
    newraw = RawDivision(new_division)
    for master_sched in master_schedules.values():
        if old_name in master_sched.rawDivisions:
            master_sched.rawDivisions.pop(old_name)
            master_sched.rawDivisions[new_division.fullName.value] = newraw
            schedules_to_change[master_sched.name] = master_sched
            for schedule in master_sched.schedules:
                if schedule.division.fullName == old_name:
                    schedule.division = newraw
                    for combo, game in schedule.games_by_combo_gen():
                        if game is None:
                            continue
                        game.division_name = new_division.fullName.value
                    for team in schedule.games_by_team:
                        for game in schedule.games_by_team[team]:
                            game.division_name = new_division.fullName.value
    edit_pickle(r,teams=teams_to_change,master_schedules=schedules_to_change)

def generate_csv_facility(facility, master_sched: MasterSchedule):
    games = []

    for schedule in master_sched.schedules:
        for date in schedule.games:
            for game in schedule.games[date]:
                if game.rfacility.fullName == facility:
                    games.append(game)
    games = sorted(games, key=lambda x: x.date)
    return "Date,Team 1,Team 2,Facility\n" + '\n'.join(
        list(map(lambda x: x.csv_display_versus_with_facility_full() if x else '', games)))

@app.route("/clone")
@htpasswd.required
def clone_team(user):
    if "team"  not in request.args:
        return "bruh"
    teams,r = load_teams()

    team = teams[request.args["team"]]
    t = Team(team.fullName.value+" clone", team.shortName.value, team.division.value,
             team.practiceDays.days, team.homeFacility.value,
             team.alternateFacility.value, repr(team.noPlayDates),
             team.noMatchDays.days, str(team.homeMatchPCT.value),
             repr(team.startDate),team.notes.value)
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in teams:
        t.fullName.value+=" (2)"
    add_pickle(r,team=t)

    return flask.redirect("/edit")
@app.route("/submitnewteam", methods=["POST"])
@htpasswd.required
def add_new_team(user):
    teams, r = load_teams()
    t = Team(request.form["fullName"], request.form["shortName"], request.form["division"],
             Weekdays.parse_weekdays(request.form, "practiceDays"), request.form["homeFacility"],
             request.form["alternativeFacility"], request.form["noPlayDates"],
             Weekdays.parse_weekdays(request.form, "noMatchDays"), request.form["homeMatchPCT"],
             request.form["startDate"],request.form["notes"])
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in teams:
        return render_template("submitnewteam_fail.html", errors=[t.fullName.value + " is already a team!"])
    teams[t.fullName.value] = t
    add_pickle(r,team=t)

    return render_template("submitnewteam.html", data=t.properties)


@app.route("/newteam", methods=["GET"])
@htpasswd.required
def newteam_page(user):
    teams,r = load_teams()
    divisions,r = load_divisions(r)
    facilities,r = load_facilities(r)
    try:
        return render_template("newteam.html", facilities=facilities,divisions=divisions,sfacs=sorted(facilities.keys(),key=lambda x:facilities[x].shortName.value.lower()),divs=sorted(divisions.keys(),key=lambda x:divisions[x].shortName.value.lower()))
    except Exception as e:
        print(e)


@app.route("/", methods=["GET"])
@htpasswd.required
def index_page(user):
    return send_from_directory("./websites", "index.html")


@app.route("/edit", methods=["POST", "GET"])
@htpasswd.required
def edit_page(user):
    teams, r = load_teams()
    if request.method == "POST":
        if request.form["delete"] not in teams:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Team does not exit!"
        divisions, r= load_divisions(r)
        facilities,r = load_facilities(r)
        master_schedules,r = load_master_schedules(r)
        delete_team(request.form["delete"],teams,divisions,facilities,master_schedules,r)
        delete_pickle(r,team=request.form["delete"])
        return flask.redirect("/edit")
    arg = request.args.get("team")
    if arg == None:
        return render_template("selectteamedit.html", teams=teams, ordered_teams=sorted(list(teams.keys()),key=str.lower))

    if arg in teams:
        facilities,r = load_facilities(r)
        divisions,r = load_divisions(r)
        return render_template("editteam.html", team=teams[arg], facilities=facilities, divisions=divisions,sfacs=sorted(facilities.keys(),key=lambda x:facilities[x].shortName.value.lower()),divs=sorted(divisions.keys(),key=lambda x:divisions[x].shortName.value.lower()))
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"


@app.route("/submitedit", methods=["POST"])
@htpasswd.required
def submit_edit_page(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    name = request.form["teamname"]
    if name in teams:

        t = Team(request.form["fullName"], request.form["shortName"], request.form["division"],
                 Weekdays.parse_weekdays(request.form, "practiceDays"), request.form["homeFacility"],
                 request.form["alternativeFacility"], request.form["noPlayDates"],
                 Weekdays.parse_weekdays(request.form, "noMatchDays"), request.form["homeMatchPCT"],
                 request.form["startDate"],request.form["notes"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)

        delete_pickle(r,team=request.form["teamname"])
        if hash(teams[name]) != hash(t):
            change_team(request.form["teamname"], t,teams, divisions, facilities, master_schedules, r)
        add_pickle(r,team=t)
        return render_template("submiteditteam.html", data=t.properties)
    return "Ok this should neve everr happen. "


@app.route("/delete", methods=["GET"])
@htpasswd.required
def delete_page(user):
    teams, r = load_teams()
    name = request.args.get("team")
    if name == None or name not in teams:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a team</h1>"

    return render_template("deleteteam.html", name=name)


@app.route("/newdivision")
@htpasswd.required
def new_division(user):
    return send_from_directory("./websites", "newdivision.html")


@app.route("/submitnewdivision", methods=["POST"])
@htpasswd.required
def submit_new_division(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    t = Division(request.form["year"], request.form["fullName"], request.form["shortName"],
                 request.form["start"], request.form["end"])
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in divisions:
        return render_template("submitnewteam_fail.html", errors=[t.fullName.value + " is already a facility!"])
    divisions[t.fullName.value] = t
    add_pickle(r,division=t)
    return render_template("submitnewdivision.html", data=t.properties)


@app.route("/editdivision", methods=["GET", "POST"])
@htpasswd.required
def edit_division(user):
    divisions, r = load_divisions()
    if request.method == "POST":
        teams,r = load_teams(r)
        if request.form["delete"] not in divisions:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Division does not exit!"
        divisions.pop(request.form["delete"])
        for team in teams:
            if teams[team].division.value == request.form["delete"]:
                teams[team].division.value = None
        delete_pickle(r,division=request.form["delete"])
        return flask.redirect("/editdivision")
    arg = request.args.get("division")
    if arg == None:
        teams,r = load_teams(r)
        teamsbydiv = {
            division: ', '.join([teams[x].fullName.value for x in teams if teams[x].division.value == divisions[division].fullName.value]) for
            division in divisions}
        return render_template("selectdivisionedit.html", divisions=divisions, ordered_divisions=sorted(list(divisions.keys()),key=str.lower),teamsbydiv=teamsbydiv)

    if arg in divisions:
        return render_template("editdivision.html", facility=divisions[arg])
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"


@app.route("/deletedivision")
@htpasswd.required
def delete_division_page(user):
    divisions, r = load_divisions()
    name = request.args.get("division")
    if name == None:
        return "fat L"
    if name not in divisions:
        return f"<a href='/'>Home</a><h1>ERROR: {html.escape(name)} is not a division</h1>"
    return render_template("deletedivision.html", name=name)


@app.route("/newfacility")
@htpasswd.required
def new_facility_page(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    return render_template("newfacility.html", teams=teams,ordered_teams=sorted(list(teams.keys()),key=lambda x: teams[x].shortName.value.lower()))


@app.route("/submitnewfacility", methods=["POST"])
@htpasswd.required
def add_new_facility(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    parsed_teams = []
    for i in range(1, len(teams)+1):
        if "team-" + str(i) in request.form:
            if request.form["team-" + str(i)] == "$none" or request.form["team-" + str(i)] in parsed_teams:
                continue
            parsed_teams.append(request.form["team-" + str(i)])
        else:
            break
    t = Facility(request.form["fullName"], request.form["shortName"],
                 Weekdays.parse_weekdays(request.form, "daysCanHost"), request.form["datesCantHost"], parsed_teams,request.form["notes"])
    if len(t.errors) > 0:
        return render_template("submitnewteam_fail.html", errors=t.errors)
    if t.fullName.value in facilities:
        return render_template("submitnewteam_fail.html", errors=[t.fullName.value + " is already a facility!"])
    facilities[t.fullName.value] = t
    add_pickle(r,facility=t)

    return render_template("submitnewfacility.html", data=t.properties)


@app.route("/editfacilities", methods=["GET", "POST"])
@htpasswd.required
def edit_facilities(user):
    facilities, r = load_facilities()
    if request.method == "POST":
        if request.form["delete"] not in facilities:
            return "<a href='/'>Home</a><br><h1>ERROR!</h1>Facility does not exit!"
        teams, divisions, facilities, master_schedules, red = load_pickle()
        delete_facility(request.form["delete"],teams, divisions, facilities, master_schedules, red)

        delete_pickle(r,facility=request.form["delete"])
        return flask.redirect("/editfacilities")
    arg = request.args.get("facility")
    if arg == None:
        return render_template("selectfacilityedit.html", teams=facilities,
                               ordered_teams=sorted(list(facilities.keys()),key=lambda x:x.lower()))

    if arg in facilities:
        teams,r = load_teams(r)
        return render_template("editfacility.html", facility=facilities[arg], teams=teams,ordered_teams=sorted(list(teams.keys()),key=lambda x: teams[x].shortName.value.lower()))
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(arg)} does not exist<br><a href='edit'>Edit</a>"


@app.route("/submiteditfacility", methods=["POST"])
@htpasswd.required
def submit_edit_facility(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    name = request.form["facilityname"]
    if name in facilities:

        parsed_teams = []
        for i in range(1, len(teams)+1):
            if "team-" + str(i) in request.form:
                if request.form["team-" + str(i)] == "$none" or request.form["team-" + str(i)] in parsed_teams:
                    continue
                parsed_teams.append(request.form["team-" + str(i)])
            else:
                break
        t = Facility(request.form["fullName"], request.form["shortName"],
                     Weekdays.parse_weekdays(request.form, "daysCanHost"), request.form["datesCantHost"], parsed_teams,request.form["notes"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)

        delete_pickle(r,facility=name)
        if hash(t)!=hash(facilities[name]):
            facilities.pop(name)
            facilities[t.fullName.value] = t
            change_facility(name, t,teams, divisions, facilities, master_schedules, r)
        add_pickle(r,facility=t)
        return render_template("submiteditfacility.html", data=t.properties)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(name)} is not a facility!!"


@app.route("/submiteditdivision", methods=["POST"])
@htpasswd.required
def submit_edit_division(user):
    teams, divisions, facilities, master_schedules, r = load_pickle()
    name = request.form["divisionname"]
    if name in divisions:

        t = Division(request.form["year"], request.form["fullName"], request.form["shortName"],
                     request.form["start"], request.form["end"])

        if len(t.errors) > 0:
            return render_template("submitnewteam_fail.html", errors=t.errors)
        divisions.pop(name)
        delete_pickle(r,division=name)
        divisions[t.fullName.value] = t
        change_division(name, t,teams, divisions, facilities, master_schedules, r)
        add_pickle(r,division=t)
        return render_template("submiteditdivision.html", data=t.properties)
    return f"<a href='/'>Home</a><br><h1>ERROR</h1>{html.escape(name)} is not a division!!"


@app.route("/deletefacility")
@htpasswd.required
def delete_facility_page(user):
    facilities,r =load_facilities()
    name = request.args.get("facility")
    if name == None or name not in facilities:
        return f"<a href='/'>Home</a> <h1>ERROR: {html.escape(name)} is not a facility</h1>"
    return render_template("deletefacility.html", name=name)


@app.route("/generateschedule", methods=["POST", "GET"])
@htpasswd.required
def generate_schedule_page(user):

    is_scheduling,is_updating,iteration_counter,current_schedule,cap_iterations = load_scheduling_data()
    if is_scheduling:
        return flask.redirect("/loadingscreenpost?name=" + urllib.parse.quote_plus(current_schedule))
    if is_updating:
        return flask.redirect("/loadingscreenupdate?name=" + urllib.parse.quote_plus(current_schedule))
    if 'iterations' in request.form:
        teams, divisions, facilities, master_schedules, r = load_pickle()
        if request.form["name"] in master_schedules:
            return "schedule with name already exists"

        teamsbydiv = {
            division: {x: teams[x] for x in teams if teams[x].division.value == divisions[division].fullName.value} for
            division in divisions}
        for division in teamsbydiv:
            if len(teamsbydiv[division]) < 2:
                return "please add more than 1 teams to the " + html.escape(division) + " division"

        generate_schedule_thread(request.form["name"], int(request.form["iterations"]))

        return render_template("loadingscreen.html", iters=iteration_counter,
                               maxiters=cap_iterations, name=request.form["name"])

    return render_template("generateschedule.html")


@app.route("/loadingscreenpost", methods=["GET"])
@htpasswd.required
def loading_screen(user):
    is_scheduling, is_updating, iteration_counter, current_schedule, cap_iterations = load_scheduling_data()


    if is_scheduling:
        return render_template("loadingscreen.html", iters=iteration_counter,
                               maxiters=cap_iterations, name=request.args["name"])
    return flask.redirect("/viewschedules?schedule=" + urllib.parse.quote_plus(request.args["name"]))


@app.route("/cancelscheduler", methods=["POST"])
@htpasswd.required
def cancel_scheduler(user):
    save_scheduling_data(is_scheduling=False)
    return flask.redirect("/")


@app.route("/viewschedules", methods=["GET", "POST"])
@htpasswd.required
def view_schedules(user):

    if "schedule" in request.args:
        master_schedules,r = load_master_schedules()
        schedu: MasterSchedule = master_schedules[request.args["schedule"]]
        divisions=[x.division.fullName for x in schedu.schedules]
        sched_by_div = {x.division.fullName:x for x in schedu.schedules}
        return render_template("scheduledisplay.html", teamsByDivs={division: sorted(list(sched_by_div[division].teams.keys()),key=lambda x:x.lower())
                                                                    for division in schedu.rawDivisions},
                               divisions=divisions,
                               scheduleArr={x.division.fullName:x.games_in_table_order() for x in schedu.schedules},
                               name=request.args["schedule"], enum=enumerate)

    master_schedules,r = load_master_schedules()
    return render_template("viewschedules.html", schedules=master_schedules)


@app.route("/downloadschedule")
@htpasswd.required
def download_schedule(user):
    teams, divisions, facilities, master_schedules, redis = load_pickle()
    if "schedule" in request.args and "division" in request.args:
        try:
            schedu: Schedule = next(x for x in master_schedules[request.args["schedule"]].schedules if
                                    x.division.fullName == request.args["division"])
        except:
            return "Invalid url"
        data = schedu.as_csv()
        return flask.Response(data,
                              mimetype="text/plain",
                              headers={"Content-Disposition":
                                           f"attachment;filename={request.args['division']}.csv"})
    if "facility" in request.args and "schedule" in request.args:
        try:
            if request.args["facility"] not in facilities:
                return "Unknown facility"
            data = generate_csv_facility(request.args["facility"],
                                         master_schedules[request.args["schedule"]])
            return flask.Response(data,
                                  mimetype="text/plain",
                                  headers={"Content-Disposition":
                                               f"attachment;filename={request.args['facility']}.csv"})
        except:
            return "Invalid url"
    if "schedule" in request.args:
        print("ok so we do be doin")
        master_sched = master_schedules[request.args["schedule"]]
        final_csv = master_sched.generate_csv()
        return flask.Response(final_csv,
                              mimetype="text/plain",
                              headers={"Content-Disposition":
                                           f"attachment;filename={request.args['schedule']}.csv"})
    return "No schedule submitted in GET request"


@app.route("/downloadbyfacility")
@htpasswd.required
def download_by_facility(user):
    teams, divisions, facilities, master_schedules, redis = load_pickle()
    if 'schedule' not in request.args:
        return "no schedule when trying to download by faciltiy"
    if request.args["schedule"] not in master_schedules:
        return "Unkown schedule: " + html.escape(request.args["schedule"])
    return render_template("downloadbyfacility.html", facilities=facilities, scheduleName=request.args["schedule"],sfacs=sorted(facilities.keys(),key=lambda x:facilities[x].shortName.value.lower()))




@app.route("/deleteschedule", methods=["GET", "POST"])
@htpasswd.required
def delete_schedule(user):
    master_schedules, r = load_master_schedules()
    if request.method == 'POST':
        if request.form["name"] in master_schedules:
            delete_pickle(r,master_schedule=request.form["name"])
            return flask.redirect("/viewschedules")

        return "error related to delete schedule"
    if "schedule" in request.args:
        if request.args["schedule"] not in master_schedules:
            return "Unknown Schedule"
        return render_template("deleteschedule.html", name=request.args["schedule"])
    return "No schedule inputted"


@app.route("/updateschedule", methods=["GET", "POST"])
@htpasswd.required
def update_schedule_page(user):
    teams, divisions, facilities, master_schedules, redis = load_pickle()
    is_scheduling, is_updating, iteration_counter, current_schedule, cap_iterations = load_scheduling_data()
    if request.method == "GET":
        if "schedule" not in request.args:
            return "Please select a schedule to update"
        if request.args["schedule"] not in master_schedules:
            return "Non-existant schedule"
        return render_template("updateschedule.html", name=request.args["schedule"])
    if is_scheduling:
        return flask.redirect("/loadingscreenpost?name=" + urllib.parse.quote_plus(current_schedule))
    if is_updating:
        return flask.redirect("/loadingscreenupdate?name=" + urllib.parse.quote_plus(current_schedule))

    generate_schedule_thread(request.form["name"], int(request.form["iterations"]), True)
    return flask.redirect("/loadingscreenupdate?name=" + urllib.parse.quote_plus(request.form["name"]))


@app.route("/loadingscreenupdate")
@htpasswd.required
def loading_screen_update(user):
    is_scheduling, is_updating, iteration_counter, current_schedule, cap_iterations = load_scheduling_data()
    if not is_updating:
        return flask.redirect("/viewschedules?schedule=" + urllib.parse.quote_plus(request.args["name"]))
    return render_template("loadingscreenupdate.html", iters=iteration_counter,
                           maxiters=cap_iterations, name=request.args["name"])


@app.route("/cancelupdater", methods=["POST"])
@htpasswd.required
def cancel_updater(user):
    save_scheduling_data(is_updating=False)

    return flask.redirect("/")


@app.route("/leaguesettings", methods=["POST", "GET"])
@htpasswd.required
def league_settings(user):
    league_wide_no_play_dates,str_league_wide_no_play_dates = load_no_play()
    if request.method == "GET":
        notes= load_league_notes()
        return render_template("leaguesettings.html", noPlayDates=str_league_wide_no_play_dates,notes=notes)
    parsed = Dates("League Wide No Play Dates", request.form["noPlayDates"])
    if parsed.error:
        return render_template("submitnewteam_fail.html", errors=[error_messages(parsed)])
    str_league_wide_no_play_dates = parsed.__repr__()
    league_wide_no_play_dates = parsed.to_set()
    save_no_play(league_wide_no_play_dates,str_league_wide_no_play_dates)
    save_league_notes(request.form["notes"])
    return render_template("leaguesettingssuccess.html", noPlayDates=str_league_wide_no_play_dates)



# teams, divisions, facilities, master_schedules, p = load_pickle_no_compression(connect_redis("redis-10752.c91.us-east-1-3.ec2.cloud.redislabs.com",10752,"wvhnHTE0DLXQqS5avbykMTvc8NZuAlNH","default"))

def load_backup():
    with open("backup.pickle","rb") as f:
        teams, divisions, facilities, master_schedules = pickle.load(f)
    r = connect_redis()
    for n,g in zip(("team","division","facility","master_schedule"),(teams, divisions, facilities, master_schedules)):
        for t in g.values():
            add_pickle(r,**{n:t})


# pickle_to_redis()
# print("cool epic on heroku")
def make_backup():
    with open("backup.pickle","wb") as f:
        pickle.dump(load_pickle()[:-1],f)
port = int(os.environ.get('PORT', 5000))  # as per OP comments default is 17995
if __name__ == "__main__":


    app.run(port=port)

#Briarcliff Boys Varsity got deleted