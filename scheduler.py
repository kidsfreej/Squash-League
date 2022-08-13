import random
from copy import copy,deepcopy
import datetime
import pickle
import bisect


from typing import List, Dict

from TeamData import *
def date_range_gen(start,end):
    r  = set()
    cur_date = start
    while cur_date!=end:
        r.add(cur_date)
        cur_date+=datetime.timedelta(days=1)
    r.add(cur_date)
    return r
teams = {}
divisions = {}
facilities = {}
rawTeams = {}
rawFacilities={}
rawDivisions={}
class RawDivision:

    def __init__(self, division:Division):
        self.year = division.year.value
        self.fullName = division.fullName.value
        self.shortName = division.shortName.value
        self.dates =   date_range_gen(division.start.to_datetime(),division.end.to_datetime())
        self.start = division.start.to_datetime()
        self.end = division.end.to_datetime()
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
    def __repr__(self):
        return f"<Raw: {self.fullName}>"
class Game:
    def __init__(self, date:datetime.datetime, team1:RawTeam, team2:RawTeam, rfacility:RawFacility):
        self.date = date
        self.rteam1 = team1
        self.rteam2 = team2
        self.rfacility :RawFacility= rfacility
    def __repr__(self):
        return f"<{Weekday.weekdays[self.date.weekday()]} {self.date} {self.rteam1.fullName} vs {self.rteam2.fullName} at {self.rfacility.fullName}>"
    def __eq__(self, other):
        return self.date ==other.date and self.rteam1 == other.rteam1 and self.rteam2==other.rteam2
    def __ne__(self, other):
        return not (self==other)
    def __deepcopy__(self, memodict={}):
        c = Game(self.date,self.rteam1,self.rteam2,self.rfacility)
        return c
    def html_display(self):
        return f"{Weekday.weekdays[self.date.weekday()].capitalize()}, {str(self.date.month)+'/'+str(self.date.day)+'/'+str(self.date.year)}   @ {self.rfacility.fullName}"
class ScoredSchedule:
    def __init__(self,schedule):
        self.schedule = schedule
        self.score = schedule.score()

    def __repr__(self):
        return f"\n<{self.score}\n{self.schedule}>"


class Schedule:
    def __init__(self,division:RawDivision,teams:Dict[str,RawTeam],facilities:Dict[str,RawFacility]):
        if division is None:
            return
        self.facilities = facilities
        self.division = division
        self.games:Dict[datetime.datetime,List[Game]] = {}
        self.games_by_team:Dict[str,List[Game]] = {}
        self.team_home_plays:Dict[str,int]= {}
        self.team_away_plays:Dict[str,int]= {}
        self.team_combos:List = []
        self.teams = teams
        for team1 in teams:
            for team2 in teams:
                if teams[team1]!=teams[team2] and (teams[team2],teams[team1]) not in self.team_combos:
                    self.team_combos.append((teams[team1],teams[team2]))
        self.max_games = len(self.team_combos)

        self.optimal_distance = self.calculate_optimal_distance()
    def calculate_optimal_distance(self):
        dist = (self.division.end-self.division.start).days.real
        avg_dist = dist/(len(self.teams)+2)
        return avg_dist
    def games_by_combo(self):
        combos = []

        for team1 in self.teams:
            for team2 in self.teams:
                if self.teams[team1]!=self.teams[team2] and (self.teams[team2],self.teams[team1]) not in combos:
                    combos.append((self.teams[team1],self.teams[team2]))
                    if team1 in self.games_by_team:
                        for game in self.games_by_team[team1]:

                            if game.rteam2.fullName == team2:
                                yield (combos[-1],game)
                                break
                        else:
                            yield (combos[-1],None)
                    else:
                        yield (combos[-1], None)

    def games_in_table_order(self):
        d = [[None for x in range(len(self.teams))] for x in range(len(self.teams))]
        x=0
        y=0
        combos = []
        for team1 in self.teams:
            for team2 in self.teams:
                if self.teams[team1]!=self.teams[team2] and (self.teams[team2],self.teams[team1]) not in combos:
                    combos.append((self.teams[team1],self.teams[team2]))
                    if team1 in self.games_by_team:
                        for game in self.games_by_team[team1]:
                            if game.rteam2.fullName == team2:
                                d[y][x] = game
                x += 1
            y += 1
            x = 0

        return d
    def add_game(self,game:Game):
        if game.date not in self.games:
            self.games[game.date] = [game]
        else:
            self.games[game.date].append(game)
        if game.rteam1.fullName not in self.games_by_team:
            self.games_by_team[game.rteam1.fullName] = [game]
        else:
            bisect.insort(self.games_by_team[game.rteam1.fullName], game,key=lambda x:x.date)
        if game.rteam2.fullName  not in self.games_by_team:
            self.games_by_team[game.rteam2.fullName] = [game]
        else:
            bisect.insort(self.games_by_team[game.rteam2.fullName],game,key=lambda x:x.date)
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
        i=0
        for g in self.games_by_team[game.rteam1.fullName]:
            if g.rteam2.fullName == game.rteam2.fullName and g.rteam1.fullName == game.rteam1.fullName:
                self.games_by_team[game.rteam1.fullName].pop(i)
                break
            i+=1
        i=0
        for g in self.games_by_team[game.rteam2.fullName]:
            if g.rteam2.fullName == game.rteam2.fullName and g.rteam1.fullName == game.rteam1.fullName:
                self.games_by_team[game.rteam2.fullName].pop(i)
                break
            i+=1
    def remove_game(self,game:Game):
        self.games[game.date].remove(game)
        self.team_home_plays[game.rteam1.fullName] -=1 if game.rfacility.fullName== game.rteam1.homeFacility else 0
        self.team_away_plays[game.rteam1.fullName] -=1 if game.rfacility.fullName!= game.rteam1.homeFacility else 0
        self.team_home_plays[game.rteam2.fullName] -=1 if game.rfacility.fullName== game.rteam2.homeFacility else 0
        self.team_away_plays[game.rteam2.fullName] -=1 if game.rfacility.fullName!= game.rteam2.homeFacility else 0
        i=0
        for g in self.games_by_team[game.rteam1.fullName]:
            if g.rteam2.fullName == game.rteam2.fullName and g.rteam1.fullName == game.rteam1.fullName:
                self.games_by_team[game.rteam1.fullName].pop(i)
                break
            i+=1
        i=0
        for g in self.games_by_team[game.rteam2.fullName]:
            if g.rteam2.fullName == game.rteam2.fullName and g.rteam1.fullName == game.rteam1.fullName:
                self.games_by_team[game.rteam2.fullName].pop(i)
                break
            i+=1
    def score(self,mute=True):
        #sum of all teams, homepct - actualpct
        #+100 everytime facility is not at alternative facility
        #+9 points for every day farther from the optimal distance for games
        if not mute:
            print(self)
        score = 0
        game_counter = 0
        for team in self.team_home_plays:
            if self.team_home_plays[team]+self.team_away_plays[team]!=0:
                score+=abs(self.team_home_plays[team]*100/(self.team_home_plays[team]+self.team_away_plays[team]) - self.teams[team].homeMatchPCT)
        if not mute:
            print("by home play pct:",score)

        temp_score=0
        for date in self.games:
            for game in self.games[date]:
                if game.rfacility.fullName!= game.rteam1.alternateFacility or game.rfacility.fullName != game.rteam2.alternateFacility:
                    temp_score+=100
                game_counter+=1
        if not mute:
            print("by not using alternate facility:", temp_score)
        score+=temp_score
        temp_score=0
        temp_score+=(self.max_games-game_counter-len(self.team_combos))*400
        if not mute:
            print("by days missing:",temp_score)
        score+=temp_score

        temp_score = 0
        for team_name in self.games_by_team:
            for i in range(len(self.games_by_team[team_name])-1):
                temp_score+=abs((self.games_by_team[team_name][i+1].date-self.games_by_team[team_name][i].date).days.real-self.optimal_distance)*9
        score += temp_score
        if not mute:
            print("by days off:",temp_score)
            print("total score:",score)
        return score
    def game_by_team_combo(self,combo):
        if combo[0].fullName in self.games_by_team:
            for g in self.games_by_team[combo[0].fullName]:
                if g.rteam1 in combo and g.rteam2 in combo:
                    return g
        return None
    def find_best(self,iters):
        schedules = []
        for i in range(iters):
            schedules.append(ScoredSchedule(self.recurse()))
        schedules.sort(key=lambda x: -x.score)
        return schedules
    def sudoku(self):
        if len(self.team_combos)==0:
            return copy(self)
        combo = self.team_combos.pop(0)
        posses = self.possible_games(combo[0],combo[1])
        if len(posses)>0:
            poss = random.choice(posses)
            self.add_game(poss)
            k =self.sudoku()
            self.remove_lastest_game(poss)
            self.team_combos.append(combo)
            return k

        c = self.sudoku()
        self.team_combos.append(combo)
        return c
    def recurse(self):
        return self.recurse()

    def possible_games(self, team1: RawTeam, team2: RawTeam) -> List[Game]:
        possible_games  = []
        for date in self.division.dates:
            if date > team1.startDate and date>team2.startDate:
                if date not in team1.noPlayDates and date not in team2.noPlayDates:
                    weekday = date.weekday()
                    if weekday not in team1.practiceDays and weekday not in team2.practiceDays:


                        for facility in self.facilities:
                            if team1.fullName in self.facilities[facility].allowedTeams and team2.fullName in self.facilities[facility].allowedTeams:
                                if weekday in self.facilities[facility].daysCanHost:
                                    if date not in self.facilities[facility].datesCantHost:
                                        if date in self.games:
                                            for game in self.games[date]:
                                                if game.rteam1.fullName ==  team1.fullName or game.rteam2.fullName == team2.fullName or game.rfacility.fullName==facility:
                                                    break
                                            else:
                                                possible_games.append(Game(date, team1, team2, self.facilities[facility]))
                                        else:
                                            possible_games.append(Game(date,team1,team2,self.facilities[facility]))
        return possible_games
    def __copy__(self):
        c = Schedule(None,None,None)
        c.division = self.division
        c.team_combos = deepcopy(self.team_combos)
        c.team_home_plays = deepcopy(self.team_home_plays)
        c.team_away_plays = deepcopy(self.team_away_plays)
        c.games = deepcopy(self.games)
        c.optimal_distance= self.optimal_distance
        c.max_games = self.max_games
        c.games_by_team = deepcopy(self.games_by_team)
        c.teams = self.teams
        c.facilities = self.facilities
        return c
    def __repr__(self):
        return f"<Schedule: {[self.games[date] for date in self.games if len(self.games[date])>0]}>"
    def generate_schedule(self,iterations,iterations_counter):
        current = self.sudoku()
        best_sched = copy(current)
        best_score = current.score()
        for i in range(iterations):
            iterations_counter[0]=i+1
            l :List[ScoredSchedule]= []
            for combo,game in current.games_by_combo():
                c = copy(current)
                if game:
                    c.remove_game(game)
                c.team_combos.insert(0,combo)
                bisect.insort(l,ScoredSchedule(c),key=lambda x:x.score)

            last_half = l[:len(l)//3]
            for scored_sched in last_half:
                combo = current.game_by_team_combo(scored_sched.schedule.team_combos[0])
                if combo:
                    current.remove_game(combo)
                current.team_combos.append(scored_sched.schedule.team_combos[0])
            current = current.sudoku()
            cur_score=current.score()

            if cur_score<best_score:
                print("here:",i,"score:",cur_score)
                best_score=cur_score
                best_sched = copy(current)
        return best_sched

# class SwapSchedule(Schedule):
#     def __init__(self,schedule:Schedule,swaps:int=0):
#         super().__init__(None,None)
#         self.division = schedule.division
#         self.team_combos = deepcopy(schedule.team_combos)
#         self.team_home_plays = deepcopy(schedule.team_home_plays)
#         self.team_away_plays = deepcopy(schedule.team_away_plays)
#         self.games = deepcopy(schedule.games)
#         self.optimal_distance= schedule.optimal_distance
#         self.max_games = schedule.max_games
#         self.games_by_team = deepcopy(schedule.games_by_team)
#         self.swaps = swaps
#     def recurse(self,backelf):trace):
#         if backtrace:
#
#         else:
#             return super().recurse()
#     def possible_backtraces(s

# with open("data.pickle", "rb") as f:
#     teams: Team = pickle.load(f)
# raw = RawTeam(teams["teamanem"],{},{})
# print(raw.startDate)
# print(raw.)

# print(teams   ["teamanem"].startDate)

# Team("fullName", "shortname", "div", Dates.from_start_end(Date.from_date(7, 1, 2022), Date.from_date(7, 29, 2022)),
#      "homefacility", "alt facilityt", )

