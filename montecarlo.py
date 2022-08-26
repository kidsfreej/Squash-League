
from __future__ import annotations

import threading

from scheduler import *
import math


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
def generate_schedule_thread(name,iterations,divisions,teams,facilities,do_update=False):

    MasterSchedule.is_updating=do_update
    MasterSchedule.is_scheduling=not do_update
    MasterSchedule.cap_iterations=iterations
    MasterSchedule.iteration_counter=0
    if not do_update:
        master = MasterSchedule(divisions, teams, facilities)
    else:
        master = MasterSchedule.master_schedules[name]

    MasterSchedule.current_schedule= name

    result = master.generate_master_schedule(iterations,do_update)


    if result:
        MasterSchedule.master_schedules[name] = result


    MasterSchedule.is_scheduling = False
    MasterSchedule.is_updating = False

