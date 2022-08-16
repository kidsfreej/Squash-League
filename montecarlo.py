
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
        if len(self.head.children)==1:
            return "no_possible"
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
    def rollout(self):

        rec = self.schedule.recurse()
        return rec.score()
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

        return add  + 1.4142 * math.sqrt(math.log(self.parent.visits) / (self.visits + 1))
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
        if len(self.schedule.team_combos)==0:
            return
        perms = self.schedule.possible_games(self.schedule.team_combos[0][0],self.schedule.team_combos[0][1])
        for perm in perms:
            c = copy(self.schedule)
            c.add_game(perm)
            c.team_combos.pop(0)
            self.children.append(ScheduleNode(self.tree, c, self))
        c=  copy(self.schedule)
        c.team_combos.pop(0)
        self.children.append(ScheduleNode(self.tree,c,self))
schedules_dict :Dict[str,Schedule]= {}

isscheduling:set = set()
isupdating = [False]
iterations_counter ={}
cap_iterations = {}
def generate_schedule(name,division:Division,iterations,teams:Dict[str,Team],facilities:Dict[str,Facility],isscheduling:set,iterations_counter,buffer:Dict[str,Schedule],isupdating):
    isupdating = False
    isscheduling.add(name)
    iterations_counter[name]=0

    s = Schedule(RawDivision(division),{x.fullName.value:RawTeam(x) for x in teams.values() if x.division.value==division.fullName.value},{x.fullName.value:RawFacility(x) for x in facilities.values()},name)
    DEBUG_s = copy(s)
    ret = s.generate_schedule(int(iterations),iterations_counter,isscheduling,name)
    if ret:
        buffer[name] = ret
        print("score:",ret.score())

    iterations_counter[name] = 0
    isscheduling.remove(name)
def update_schedule(schedule:Schedule,iterations,isscheduling:set,iterations_counter,buffer:Dict[str,Schedule],isupdating):
    isscheduling.add(schedule.name)
    isupdating[0] = True
    iterations_counter[schedule.name] =0
    c=  copy(schedule)
    c=c.update_schedule(int(iterations),iterations_counter,isscheduling)


    buffer[schedule.name] = c
    iterations_counter[schedule.name] = 0
    isscheduling.remove(schedule.name)
    isupdating[0] = False
