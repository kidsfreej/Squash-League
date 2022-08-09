
from __future__ import annotations

import threading

from scheduler import *
import math

class ScheduleTree:
    def __init__(self,schedule):
        self.head = ScheduleNode(self, schedule, None)
    def run(self):
        if len(self.head.children)==0:
            self.head.create_children()
        if not self.head.schedule.recurse():
            return "no possible"
        self.head.selection()

    def ranked(self):
        return [x.schedule for x in sorted(self.head.children,key=lambda x:x.visits)]
class ScheduleNode:
    def __init__(self, tree:ScheduleTree, schedule:Schedule, parent:ScheduleNode):
        self.tree =tree
        self.schedule = schedule
        self.children :List[ScheduleNode]= []
        self.score = 0
        self.visits = 0
        self.parent = parent
        self.no_possible = False
    def rollout(self):
        if self.no_possible:
            return -1
        rec = self.schedule.recurse()
        if rec:
            return rec.score()
        self.no_possible =True
        return -1
    def highest_uct_child(self) -> ScheduleNode:
        maxv = -999999
        maxc = None
        for child in self.children:
            uct = child.uct()
            if uct>maxv:
                maxv=  uct
                maxc = child
        return maxc
    def uct(self):


        if self.visits == 0:
            add = 0

        else:
            add = self.score / self.visits

        return add  * 1.4142 * math.sqrt(math.log(self.parent.visits) / (self.visits + 1))
    def selection(self):

        self.visits+=1
        if len(self.children)==0:
            self.create_children()
            score = self.rollout()
            self.score+=score
            return score
        child = self.highest_uct_child()
        score = child.selection()
        self.score+=score
        return score
    def create_children(self):
        if len(self.schedule.team_combos)==0 or self.no_possible:
            return
        perms = self.schedule.possible_games(self.schedule.team_combos[0][0],self.schedule.team_combos[0][1])
        for perm in perms:
            c = copy(self.schedule)
            c.add_game(perm)
            c.team_combos.pop(0)
            self.children.append(ScheduleNode(self.tree, c, self))

schedules_dict :Dict[str,Schedule]= {}

isscheduling = [False]
iterations_counter =[0]
cap_iterations = 0
def generate_schedule(name,division:Division,iterations,teams:Dict[str,Team],facilities:Dict[str,Facility],isscheduling,iterations_counter,buffer:Dict[str,Schedule]):

    isscheduling[0]=True


    s = Schedule(RawDivision(division),{x.fullName.value:RawTeam(x) for x in teams.values() if x.division.value==division.fullName.value},{x.fullName.value:RawFacility(x) for x in facilities.values()})
    c=0
    k=0
    while len(s.team_combos)>0:
        t = ScheduleTree(s)
        for i in range(iterations):
            c+=1
            k+=1
            iterations_counter[0] = c
            if isscheduling==[False]:
                return
            if t.run()=="no_possible":
                s.team_combos.pop(0)
                c = k*iterations
                break
        else:
            s = t.ranked()[0]
    buffer[name] = s

    iterations_counter[0] = 0
    isscheduling[0] = False
# ateam = rawTeams["a team"]
# bteam = rawTeams["B TEAM"]
#
# div = rawDivisions["division"]
# rawDivisions["division"]=div
# ogschedule = Schedule(div,list(rawTeams.values()))
# schedule =copy(ogschedule)
# while len(schedule.team_combos)>0:
#     t=  ScheduleTree(schedule)
#     for i in range(100):
#         t.run()
#     schedule = t.ranked()[0]
# print(schedule.games_in_table_order())
# print(schedule)

