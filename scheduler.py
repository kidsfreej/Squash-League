from copy import copy,deepcopy
import datetime
import pickle

from typing import List, Dict

from TeamData import *
from server import *
def date_range_gen(start,end):
    r  = set()
    cur_date = start
    while cur_date!=end:
        r.add(cur_date)
        cur_date+=datetime.timedelta(days=1)
    r.add(cur_date)
    return r

rawTeams = {}
rawFacilities={}
rawDivisions={}
class RawDivision:

    def __init__(self, division:Division):
        self.year = division.year.value
        self.fullName = division.fullName.value
        self.shortName = division.shortName.value
        self.dates =   date_range_gen(division.start.to_datetime(),division.end.to_datetime())
    def __eq__(self, other):
        return self.fullName == other.fullName
    def __ne__(self, other):
        return self.fullName != other.fullName
class RawFacility:
    def __init__(self,facility:Facility):
        self.fullName = facility.fullName.value
        self.shortName = facility.shortName.value
        self.daysCanHost = facility.daysCanHost.to_weekday_arr()
        self.datesCantHost = facility.datesCantHost.to_set()
        self.allowedTeams : List[str] = facility.allowedTeams.value
    def __eq__(self, other):
        return self.fullName == other.fullName
    def __ne__(self, other):
        return self.fullName != other.fullName
class RawTeam:
    def __init__(self,team:Team):
        self.fullName =  team.fullName.value
        self.shortName = team.shortName.value

        self.division = team.division.value
        self.practiceDays =team.practiceDays.to_weekday_arr()

        self.homeFacility = team.homeFacility.value

        self.alternateFacility = team.alternateFacility.value

        self.noPlayDates =team.noPlayDates.to_set()
        self.noMatchDays = team.noMatchDays.to_weekday_arr()
        self.homeMatchPCT = team.homeMatchPCT.value
        self.startDate = team.startDate.to_datetime()
    def __eq__(self, other):
        return self.fullName==other.fullName
    def __ne__(self, other):
        return self.fullName != other.fullName

class Game:
    def __init__(self, date:datetime.datetime, team1:RawTeam, team2:RawTeam, rfacility:RawFacility):
        self.date = date
        self.rteam1 = team1
        self.rteam2 = team2
        self.rfacility :RawFacility= rfacility
    def __repr__(self):
        return f"<{Weekday.weekdays[self.date.weekday()]    } {self.date} {self.rteam1.fullName} vs {self.rteam2.fullName} at {self.rfacility.fullName}>"
    def __eq__(self, other):
        return self.date ==other.date and self.rteam1 == other.rteam1
    def __ne__(self, other):
        return not (self==other)
    def __deepcopy__(self, memodict={}):
        c = Game(self.date,self.rteam1,self.rteam2,self.rfacility)
        return c
class Schedule:
    def __init__(self,division:RawDivision,teams:List[RawTeam]):
        if division is None:
            return
        self.division = division
        self.games:Dict[datetime.datetime,List[Game]] = {}
        self.team_home_plays:Dict[str,int]= {}
        self.team_away_plays:Dict[str,int]= {}
        self.team_combos:List = []
        for team1 in teams:
            for team2 in teams:
                if team1!=team2 and (team2,team1) not in self.team_combos:
                    self.team_combos.append((team1,team2))

    def add_game(self,game:Game):
        if game.date not in self.games:
            self.games[game.date] = [game]
        else:
            self.games[game.date].append(game)
        for team in [game.rteam1,game.rteam2]:
            if team.fullName not in self.team_home_plays:
                self.team_home_plays[team.fullName] = 1 if game.rfacility.fullName== team.homeFacility else 0
                self.team_away_plays[team.fullName] = 1 if game.rfacility.fullName!= team.homeFacility else 0
            else:
                self.team_home_plays[team.fullName] += 1 if game.rfacility.fullName == team.homeFacility else 0
                self.team_away_plays[team.fullName] += 1 if game.rfacility.fullName != team.homeFacility else 0

    def remove_lastest_game(self,game:Game):
        self.games[game.date].pop()
        self.team_home_plays[game.rteam1.fullName] -=1 if game.rfacility.fullName== game.rteam1.homeFacility else 0
        self.team_away_plays[game.rteam1.fullName] -=1 if game.rfacility.fullName!= game.rteam1.homeFacility else 0
        self.team_home_plays[game.rteam2.fullName] -=1 if game.rfacility.fullName== game.rteam2.homeFacility else 0
        self.team_away_plays[game.rteam2.fullName] -=1 if game.rfacility.fullName!= game.rteam2.homeFacility else 0
        # self.team_combos.append((game.rteam1,game.rteam2))
    def score(self):
        score = 0
        for team in self.team_home_plays:
            score+=abs(self.team_home_plays[team]*100/(self.team_home_plays[team]+self.team_away_plays[team]) - rawTeams[team].homeMatchPCT)

        return score
    def recurse(self,return_arr):
        if len(self.team_combos)==0:
            return_arr.append(copy(self))
            print(self)
            return
        combo = self.team_combos.pop(0)
        posses = self.possible_games(combo[0],combo[1],rawFacilities)
        if len(posses)>0:
            for poss in posses:
                self.add_game(poss)
                self.recurse(return_arr)
                self.remove_lastest_game(poss)



    def possible_games(self, team1: RawTeam, team2: RawTeam, rawFacilities : Dict[str, RawFacility]) -> List[Game]:
        possible_games  = []
        for date in self.division.dates:
            if date > team1.startDate and date>team2.startDate:
                if date not in team1.noPlayDates and date not in team2.noPlayDates:
                    weekday = date.weekday()
                    if weekday not in team1.practiceDays and weekday not in team2.practiceDays:


                        for facility in rawFacilities:
                            if team1.fullName in rawFacilities[facility].allowedTeams and team2.fullName in rawFacilities[facility].allowedTeams:
                                if weekday in rawFacilities[facility].daysCanHost:
                                    if date not in rawFacilities[facility].datesCantHost:
                                        if date in self.games:
                                            for game in self.games[date]:
                                                if game.rteam1 ==  team1 or game.rteam2 == team2 or game.rfacility.fullName==facility:
                                                    break
                                            else:
                                                possible_games.append(Game(date, team1, team2, rawFacilities[facility]))
                                        else:
                                            possible_games.append(Game(date,team1,team2,rawFacilities[facility]))
        return possible_games
    def __copy__(self):
        c = Schedule(None,None)
        c.division = self.division
        c.team_combos = deepcopy(self.team_combos)
        c.team_home_plays = deepcopy(self.team_home_plays)
        c.team_away_plays = deepcopy(self.team_away_plays)
        c.games = deepcopy(self.games)
    def __repr__(self):
        return f"<Schedule: {[self.games[date] for date in self.games if len(self.games[date])>0]}>"
for team in teams:
    rawTeams[teams[team].fullName.value] = RawTeam(teams[team])
for div in divisions:
    rawDivisions[divisions[div].fullName.value] = RawDivision(divisions[div])

for fac in facilities:
    rawFacilities[facilities[fac].fullName.value] = RawFacility(facilities[fac])

ateam = rawTeams["a team"]
bteam = rawTeams["B TEAM"]

div = rawDivisions["division"]
rawDivisions["division"]=div
schedule = Schedule(div,list(rawTeams.values()))
# print(schedule.possible_games(ateam,bteam,rawFacilities))
rarr = []
schedule.recurse(return_arr=rarr)
print(rarr)
d = copy(schedule)
# with open("data.pickle", "rb") as f:
#     teams: Team = pickle.load(f)
# raw = RawTeam(teams["teamanem"],{},{})
# print(raw.startDate)
# print(raw.)

# print(teams   ["teamanem"].startDate)

# Team("fullName", "shortname", "div", Dates.from_start_end(Date.from_date(7, 1, 2022), Date.from_date(7, 29, 2022)),
#      "homefacility", "alt facilityt", )
t = threading.Thread(target=deubg_pickle)
t.start()
app.run()
