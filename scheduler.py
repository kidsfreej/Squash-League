from __future__ import annotations
import random
from copy import copy,deepcopy
import datetime
import pickle
import bisect
import math
import matplotlib.pyplot as plt
from typing import List, Dict

from TeamData import *
import matplotlib.pyplot as plt
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
    def __hash__(self):
        return hash(self.fullName)
class Game:
    def __init__(self, date:datetime.datetime, team1:RawTeam, team2:RawTeam, rfacility:RawFacility,division_name:str):
        self.date = date
        self.rteam1 = team1
        self.rteam2 = team2
        self.rfacility :RawFacility= rfacility
        self.division_name = division_name
    def __repr__(self):
        return f"<{Weekday.weekdays[self.date.weekday()]} {self.date} {self.rteam1.fullName} vs {self.rteam2.fullName} at {self.rfacility.fullName}>"
    def __eq__(self, other):
        return self.date ==other.date and self.rteam1.fullName == other.rteam1.fullName and self.rteam2.fullName==other.rteam2.fullName and self.rfacility.fullName==other.rfacility.fullName
    def __ne__(self, other):
        return not (self==other)
    def __deepcopy__(self, memodict={}):
        c = Game(self.date,self.rteam1,self.rteam2,self.rfacility,self.division_name)
        return c
    def csv_display_versus_with_facility(self):
        return f'"{self.date.strftime("%m/%d/%y")}","{self.rteam1.shortName}","{self.rteam2.shortName}","{self.rfacility.fullName}"'
    def csv_display_versus_no_facility(self):
        return f'"{self.rteam1.shortName} v {self.rteam2.shortName}"'
    def html_display(self):
        return f"{Weekday.weekdays[self.date.weekday()].capitalize()}, {str(self.date.month)+'/'+str(self.date.day)+'/'+str(self.date.year)}   @ {self.rfacility.fullName}"
class ScoredSchedule:
    def __init__(self,schedule:Schedule):
        self.schedule = schedule
        self.score = schedule.score()

    def __repr__(self):
        return f"\n<{self.score}\n{self.schedule}>"

class RemovedSchedule:
    def __init__(self,combo,score):
        self.combo = combo
        self.score =score

class Schedule:
    league_wide_no_play_dates = set()
    str_league_wide_no_play_dates:str = ""
    def __init__(self,division:RawDivision,teams:Dict[str,RawTeam],facilities:Dict[str,RawFacility],master_schedule:MasterSchedule):

        if division is None:
            return
        self.DEBUG_iterations = []
        self.master_schedule = master_schedule
        self.facilities = facilities
        self.division = division
        self.games:Dict[datetime.datetime,List[Game]] = {}
        self.games_by_team:Dict[str,List[Game]] = {}
        self.team_home_plays:Dict[str,int]= {}
        self.team_away_plays:Dict[str,int]= {}
        self.team_combos:List = []
        self.teams = teams
        self.games_by_combo:Dict[tuple[RawTeam,RawTeam],Game] = {}
        for team1 in teams:
            for team2 in teams:
                if teams[team1]!=teams[team2] and (teams[team2],teams[team1]) not in self.team_combos:
                    self.team_combos.append((teams[team1],teams[team2]))

                    self.games_by_combo[(teams[team1], teams[team2])] =None
        self.max_games = len(self.team_combos)
        self.optimal_distance = self.calculate_optimal_distance()
    def calculate_optimal_distance(self):
        dist = (self.division.end-self.division.start).days.real
        avg_dist = dist/(len(self.teams)+2)
        return avg_dist
    def games_by_combo_gen(self):
        return self.games_by_combo.items()
    def games_in_table_order(self):
        d = [[None for x in range(len(self.teams))] for x in range(len(self.teams))]
        x=0
        y=0
        combos = []
        for team1 in self.teams:
            for team2 in self.teams:
                if self.teams[team1]!=self.teams[team2]:
                    if team1 in self.games_by_team:
                        for game in self.games_by_team[team1]:
                            if game.rteam2.fullName == team2:
                                d[y][x] = game
                                d[x][y]=game
                x += 1
            y += 1
            x = 0

        return d
    def as_csv(self):
        ordered= list(self.teams.keys())
        s="\n"+","*(len(self.teams)//2)+self.division.fullName+"\n"
        s+= ","+",".join(ordered)
        d = self.games_in_table_order()
        for y in range(len(d)):
            s+="\n\""+ordered[y]+"\","+",".join(list(map(lambda x:'"' + x.html_display()+'"' if x is not None else "-",d[y])))
        return s
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
    def     remove_game(self,game:Game):
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
                score+=abs(self.team_home_plays[team]*100/(self.team_home_plays[team]+self.team_away_plays[team]) - self.teams[team].homeMatchPCT)*10
        if not mute:
            print("by home play pct:",score)

        temp_score=0
        for date in self.games:
            for game in self.games[date]:
                if (game.rteam1.homeFacility != game.rfacility.fullName  and game.rfacility.fullName!= game.rteam1.alternateFacility and game.rteam1.alternateFacility!= None ) and (game.rteam2.homeFacility != game.rfacility.fullName and game.rfacility.fullName != game.rteam2.alternateFacility and game.rteam1.alternateFacility!= None):
                    temp_score+=100
                game_counter+=1
        if not mute:
            print("by not using alternate facility:", temp_score)
        score+=temp_score
        temp_score=0
        temp_score+=(self.max_games-game_counter-len(self.team_combos))*50
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
    def game_by_team_combo(self,combo) -> Game:
        return self.games_by_combo[combo]
    def find_best(self,iters):
        schedules = []
        for i in range(iters):
            schedules.append(ScoredSchedule(self.recurse()))
        schedules.sort(key=lambda x: -x.score)
        return schedules
    def sudoku_copy(self):
        if len(self.team_combos)==0:
            return copy(self)
        combo = self.team_combos.pop(0)
        posses = self.possible_games(combo[0],combo[1])
        if len(posses)>0:
            poss = random.choice(posses)
            self.add_game(poss)
            self.games_by_combo[combo] = poss
            k =self.sudoku_copy()
            self.remove_lastest_game(poss)
            self.team_combos.append(combo)
            self.games_by_combo[combo] = None
            return k

        self.games_by_combo[combo] = None
        c = self.sudoku_copy()
        self.team_combos.append(combo)
        return c
    def sudoku_no_copy(self):
        if len(self.team_combos)==0:
            return
        combo = self.team_combos.pop(0)
        posses = self.possible_games(combo[0],combo[1])
        if len(posses)>0:
            poss = random.choice(posses)
            self.add_game(poss)
            self.games_by_combo[combo] = poss
            self.sudoku_no_copy()
            return

        self.sudoku_no_copy()
        return
    def recurse(self):
        return self.recurse()

    def possible_games(self, team1: RawTeam, team2: RawTeam) -> List[Game]:
        possible_games  = []
        for date in self.division.dates:
            if date > team1.startDate and date>team2.startDate:
                if date not in team1.noPlayDates and date not in team2.noPlayDates and date not in Schedule.league_wide_no_play_dates:
                    weekday = date.weekday()
                    if weekday not in team1.practiceDays and weekday not in team2.practiceDays:


                        for facility in self.facilities:

                            if team1.homeMatchPCT >99 and team1.homeFacility!=facility or team2.homeMatchPCT>99 and team2.homeFacility!=facility:
                                continue

                            if facility in self.master_schedule.games_occupied_by_facility and date in self.master_schedule.games_occupied_by_facility[facility]:
                                continue
                            c=  False
                            if date in self.games:
                                for g in self.games[date]:
                                    if g.rfacility.fullName == facility:
                                        c = True
                                        break
                            if c:
                                continue
                            if not(len(self.facilities[facility].allowedTeams)==0 or team1.fullName in self.facilities[facility].allowedTeams or team2.fullName in self.facilities[facility].allowedTeams):
                                continue
                            if weekday not in self.facilities[facility].daysCanHost:
                                continue
                            if date in self.facilities[facility].datesCantHost:
                                continue
                            if date in self.games:
                                for game in self.games[date]:
                                    if game.rteam1.fullName ==  team1.fullName or game.rteam2.fullName == team2.fullName or game.rfacility.fullName==facility:
                                        break
                                else:
                                    possible_games.append(Game(date, team1, team2, self.facilities[facility],self.division.fullName))
                            else:
                                possible_games.append(Game(date,team1,team2,self.facilities[facility],self.division.fullName))
        return possible_games
    def valid(self,game:Game):
        if game.date > game.rteam1.startDate and game.date> game.rteam2.startDate:
            if game.date not in game.rteam1.noPlayDates and game.date not in game.rteam2.noPlayDates and game.date not in Schedule.league_wide_no_play_dates:
                weekday = game.date.weekday()
                if weekday not in game.rteam1.practiceDays and weekday not in game.rteam2.practiceDays:
                    if game.rteam1.homeMatchPCT >99 and game.rteam1.homeFacility!=game.rfacility.fullName or game.rteam2.homeMatchPCT>99 and game.rteam2.homeFacility!=game.rfacility.fullName:
                        return False
                    if not(len(self.facilities[game.rfacility.fullName].allowedTeams)==0 or game.rteam1.fullName in self.facilities[game.rfacility.fullName].allowedTeams or game.rteam2.fullName in self.facilities[game.rfacility.fullName].allowedTeams):
                        return False
                    if weekday not in self.facilities[game.rfacility.fullName].daysCanHost:
                        return False
                    if game.date in self.facilities[game.rfacility.fullName].datesCantHost:
                        return False
                    if game.rfacility.fullName not in self.master_schedule.rawFacilities:
                        return False
                    if game.date in self.games:
                        for og in self.games[game.date]:
                            if (game.rteam1.fullName ==  og.rteam1.fullName or game.rteam2.fullName == og.rteam2.fullName or game.rfacility.fullName==og.rfacility.fullName) and og!=game:
                                return False
                        else:
                            return True
                    else:
                        return True
        return False
    # def update_schedule(self,iterations,iterations_counter,isscheduling):
    #     games_to_change:List[Game]=[]
    #     combos_to_change= []
    #     for combo, game in self.games_by_combo():
    #         if game is None or not  self.valid(game):
    #             combos_to_change.append(combo)
    #             games_to_change.append(game)
    #     if len(combos_to_change)==0:
    #         return copy(self)
    #     current = copy(self)
    #     for combo,game in zip(combos_to_change,games_to_change):
    #         if game:
    #             current.remove_game(game)
    #         current.team_combos.append(combo)
    #     current= current.sudoku()
    #     visits_by_combo = {}
    #     for combo, game in current.games_by_combo():
    #         visits_by_combo[combo]=0
    #     best_sched = copy(current)
    #     best_score = current.score()
    #     for i in range(iterations):
    #         if self.name not in isscheduling:
    #             return
    #         iterations_counter[self.name] = i + 1
    #         l: List[ScoredSchedule] = []
    #         for combo, _ in zip(combos_to_change,games_to_change):
    #             c = copy(current)
    #             game = c.game_by_team_combo(combo)
    #             if game:
    #                 c.remove_game(game)
    #             c.team_combos.insert(0, combo)
    #             l.append(ScoredSchedule(c))
    #         ordered = sorted(l, key=lambda x: x.score)
    #
    #         index = 0
    #         while visits_by_combo[ordered[index].schedule.team_combos[0]] / (
    #                 i + 1) > 1/len(ordered) * 1.5:
    #             index += 1
    #
    #         to_remove = [ordered[index]]
    #
    #         for scored_sched in to_remove:
    #
    #             combo = current.game_by_team_combo(scored_sched.schedule.team_combos[0])
    #             visits_by_combo[scored_sched.schedule.team_combos[0]] += 1
    #             if combo:
    #                 current.remove_game(combo)
    #             current.team_combos.append(scored_sched.schedule.team_combos[0])
    #         current = current.sudoku()
    #         cur_score = current.score()
    #         if cur_score < best_score:
    #             best_score = cur_score
    #             best_sched = copy(current)
    #
    #     print("FINAL SCORE:")
    #     best_sched.score(False)
    #
    #     for game in games_to_change:
    #         if game:
    #             self.master_schedule.games_occupied_by_facility[game.rfacility.fullName].pop(game.date)
    #     for combo,game in best_sched.games_by_combo():
    #         if combo in combos_to_change and game:
    #             if game.rfacility.fullName not in self.master_schedule.games_occupied_by_facility:
    #                 self.master_schedule.games_occupied_by_facility[game.rfacility.fullName]={}
    #             self.master_schedule.games_occupied_by_facility[game.rfacility.fullName][game.date] = game
    #     return best_sched
    def __copy__(self):
        c = Schedule(None,None,None,None)
        c.division = self.division
        c.games_by_combo = deepcopy(self.games_by_combo)
        c.team_combos = deepcopy(self.team_combos)
        c.team_home_plays = deepcopy(self.team_home_plays)
        c.team_away_plays = deepcopy(self.team_away_plays)
        c.games = deepcopy(self.games)
        c.optimal_distance= self.optimal_distance
        c.max_games = self.max_games
        c.games_by_team = deepcopy(self.games_by_team)
        c.teams = self.teams
        c.facilities = self.facilities
        c.DEBUG_iterations = self.DEBUG_iterations
        c.master_schedule=self.master_schedule
        return c
    def __repr__(self):
        return f"<Schedule: {[self.games[date] for date in self.games if len(self.games[date])>0]}>"
    def update_games_occupied_by_facility(self):
        for date in self.games:
            for g in self.games[date]:
                if g.rfacility.fullName not in self.master_schedule.games_occupied_by_facility:
                    self.master_schedule.games_occupied_by_facility[g.rfacility.fullName] = {}
                self.master_schedule.games_occupied_by_facility[g.rfacility.fullName][date]=g
    def remove_game_occupied_by_facility(self,game:Game):
        self.master_schedule.games_occupied_by_facility[game.rfacility.fullName].pop(game.date)
    def add_game_occupied_by_facility(self,g:Game):
        if g.rfacility.fullName not in self.master_schedule.games_occupied_by_facility:
            self.master_schedule.games_occupied_by_facility[g.rfacility.fullName] = {}
        self.master_schedule.games_occupied_by_facility[g.rfacility.fullName][g.date] = g
    def generate_schedule(self,iterations,do_update:bool,only_combos:List[tuple[RawTeam,RawTeam]]=None):
        master_schedule_index = self.master_schedule.schedules.index(self)
        best_games_occupied_by_facility= {}
        if do_update:
            games_to_change:List[Game]=[]
            combos_to_change= []
            for combo, game in self.games_by_combo_gen():
                if game is None or not  self.valid(game):
                    combos_to_change.append(combo)
                    games_to_change.append(game)
            if len(combos_to_change) == 0:
                return copy(self)
            current = copy(self)
            for combo, game in zip(combos_to_change, games_to_change):
                if game:
                    current.remove_game(game)
                current.team_combos.append(combo)
                current.games_by_combo[combo] = None

        DEBUG_scores = []
        best_score = 99999999
        visits_by_combo  ={}
        if do_update:
            current :Schedule= current.sudoku_copy()
        else:
            current = self.sudoku_copy()

        best_sched = current
        self.master_schedule.schedules[master_schedule_index] = current
        for combo, game in current.games_by_combo_gen():
            visits_by_combo[combo]=0



        for i in range(iterations):

            MasterSchedule.iteration_counter+=1
            current = self.master_schedule.schedules[master_schedule_index]
            lowest_removed=None
            lowest_score = 99999

            if do_update or only_combos is not None:
                for combo in (combos_to_change if do_update else only_combos):
                    if visits_by_combo[combo]/(i+1)>1/len(combos_to_change if do_update else only_combos)*1.5:
                        continue
                    game:Game = current.games_by_combo[combo]
                    if game:
                        current.remove_game(game)
                    current.team_combos.append(combo)
                    t_score = current.score()
                    if lowest_score>t_score:
                        lowest_score = t_score
                        lowest_removed=  RemovedSchedule(combo,t_score)
                    if game:
                        current.add_game(game)
                    current.team_combos.pop()
            else:
                for combo,game in current.games_by_combo_gen():
                    if visits_by_combo[combo]/(i+1)>1/current.max_games*1.5:
                        continue
                    if game:
                        current.remove_game(game)

                    current.team_combos.append(combo)

                    t= current.score()
                    if t<lowest_score:
                        lowest_removed = RemovedSchedule(combo,t)
                        lowest_score=t
                    if game:
                        current.add_game(game)
                    current.team_combos.pop()


            removed_sched = lowest_removed
            visits_by_combo[removed_sched.combo] += 1

            # remove best one
            combo = removed_sched.combo
            game = current.game_by_team_combo(combo)

            if game:
                current.remove_game(game)
            current.team_combos.append(combo)
            current.games_by_combo[combo]=None
            # re sudoku and score and update games occupied by facility
            current.sudoku_no_copy()

            cur_score = current.score()
            DEBUG_scores.append(cur_score)
            game = current.game_by_team_combo(combo)
            if cur_score<best_score:
                best_score = cur_score
                best_sched=copy(current)

            current.DEBUG_iterations.append(cur_score)
        return best_sched


class MasterSchedule:
    is_scheduling = False
    is_updating = False
    iteration_counter = -1
    master_schedules :Dict[str,MasterSchedule]={}
    current_schedule = None
    cap_iterations = -1
    def __init__(self,divisions:List[Division],teams:List[Team],facilities:List[Facility]):
        if divisions is None:
            return
        self.rawDivisions = {x.fullName:x for x in map(lambda x:RawDivision(divisions[x]),divisions)}
        self.rawTeams:Dict[str,RawTeam] = {x.fullName:x for x in map(lambda x:RawTeam(teams[x]),teams)}
        self.rawFacilities = {x.fullName:x for x in map(lambda x:RawFacility(facilities[x]),facilities)}
        self.games_occupied_by_facility: Dict[str, dict[datetime.datetime,Game]] = {}

        self.schedules : List[Schedule]= [Schedule(self.rawDivisions[div],{x:self.rawTeams[x] for x in self.rawTeams if self.rawTeams[x].division==div},self.rawFacilities,self) for div in self.rawDivisions]
        self.creationDate = "never"
    def conflicts(self)->Dict[str,Dict[datetime.datetime,List[Game]]]:
        shuffled = [x for x in self.schedules]
        games_dict = {}
        for sched in shuffled:
            for date in sched.games:
                for game in sched.games[date]:
                    if game.rfacility.fullName not in games_dict:
                        games_dict[game.rfacility.fullName]={}
                    if game.date not in games_dict[game.rfacility.fullName]:
                        games_dict[game.rfacility.fullName][date] = [game]
                    else:
                        games_dict[game.rfacility.fullName][date].append(game)
        return games_dict

    def generate_master_schedule(self,iterations,do_update):
        start_iters = iterations
        current_iters=  start_iters
        for i,x in list(enumerate(self.schedules))[::-1]:
            print(self.schedules[i].division.fullName)
            self.schedules[i]=x.generate_schedule(int(iterations), do_update)
        schedules_by_division:Dict[str,Schedule] = {x.division.fullName:x for x in self.schedules}

        # #remove conflicts
        while True:
            plt.axvline(x=len(self.schedules[0].DEBUG_iterations))
            removes_by_divisions:Dict[str,List[tuple[RawTeam,RawTeam]]] = {}
            conflicts= self.conflicts()
            remove_counter = 0
            for facility in conflicts:
                for date,games in conflicts[facility].items():
                    if len(games)==1:
                        continue
                    lowest_diff = -99999
                    lowest_game = None
                    for game in games:
                        sched = schedules_by_division[game.division_name]
                        before_score = sched.score()

                        combo = (game.rteam1,game.rteam2)
                        if game:
                            sched.remove_game(game)

                        sched.team_combos.append(combo)

                        t = sched.score()-before_score
                        if t > lowest_diff:
                            lowest_game = game
                            lowest_diff = t
                        if game:
                            sched.add_game(game)
                        sched.team_combos.pop()

                    for game in games:
                        if game is lowest_game:
                            continue
                        if game.division_name not in removes_by_divisions:
                            removes_by_divisions[game.division_name] =[]
                        removes_by_divisions[game.division_name].append((game.rteam1,game.rteam2))
                        schedules_by_division[game.division_name].remove_game(game)
                        schedules_by_division[game.division_name].team_combos.append((game.rteam1,game.rteam2))
                        remove_counter+=1
            if remove_counter==0:
                break
            self.games_occupied_by_facility = {}
            for sched in self.schedules:
                sched.update_games_occupied_by_facility()

            for i,sched in enumerate(self.schedules):
                if sched.division.fullName not in removes_by_divisions:
                    continue
                self.schedules[i]=sched.generate_schedule(int(iterations)//len(self.rawTeams),False,removes_by_divisions[sched.division.fullName])
                schedules_by_division[self.schedules[i].division.fullName] = self.schedules[i]

        for sched in self.schedules:
            sched.score(False)
            plt.plot(sched.DEBUG_iterations)
            plt.text(len(sched.DEBUG_iterations),sched.DEBUG_iterations[-1],sched.division.fullName)
        # plt.savefig("images/epic.png")
        self.creationDate = datetime.datetime.now().strftime("%I:%M, %m/%d/%y")
        return self
    def score_master(self):
        return sum(map(lambda x:x.score(),self.schedules))
    def __copy__(self):
        c = MasterSchedule(None,None,None)
        c.rawTeams = self.rawTeams
        c.rawDivisions = self.rawDivisions
        c.rawFacilities = self.rawFacilities
        c.schedules = list(map(copy,self.schedules))
        return c
    def is_available_facility_as_str(self,rawFacility:RawFacility,date:datetime.datetime):

        if date in rawFacility.datesCantHost:
            return "not available"
        if date.weekday() not in rawFacility.daysCanHost:
            return "not available"
        for sched in self.schedules:
            if date in sched.games:
                for game in sched.games[date]:
                    if game.rfacility.fullName == rawFacility.fullName:
                        return game.csv_display_versus_no_facility()
        return ""


    def generate_csv(self):
        dates = {}
        for sched in self.schedules:
            for date in sched.games:
                if len(sched.games[date])>0:
                    dates[date] = sched.games[date]
        print("1")
        facilities_list = list(self.rawFacilities.values())
        master_csv = "Dates,"+','.join(map(lambda fac:'"'+fac.fullName+ (" - only "+', '.join(fac.allowedTeams)+" matches" if len(fac.allowedTeams)>0 else "")+'"',facilities_list))+"\n"
        i=0
        print("2")
        for date,game in sorted(list(dates.items()),key=lambda x: x[0]):
            master_csv+='"'+date.strftime("%m/%d/%y")+'",'+','.join(map(MasterSchedule.is_available_facility_as_str,iter(lambda:self,1),facilities_list,iter(lambda:date,1)))+"\n"
            i+=1
        print("3")
        while i< len(self.rawTeams)*3:
            master_csv+=","*len(self.rawFacilities)+"\n"
            i+=1
        print("4")
        csves = '\n\n\n'.join(map(Schedule.as_csv,self.schedules))
        print("5")
        master_csv='\n'.join(map(lambda a,b:a+",,,"+b,master_csv.split("\n"),csves.split("\n")))
        return master_csv
