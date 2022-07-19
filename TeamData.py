import html

# TODO Web page (flask) as input/UI
# TODO
properties = ["Team Name", "Abbreviated Name", "Division", "Practice Days", "Home Facility",
              "Alternate Facility", "No Play Dates", "No Match Days", "Home Match %", "Start Date"]
# test
class Prop:
    def __init__(self,name:str,value):
        self.name = name
        self.value = value
        self.error = False
    def __repr__(self):
        return repr(self.value)
class Date:
    def __int__(self,name:str,value:str):
        self.name = name
        self.error=  False
        split = value.split("/")
        try:
            self.day = int(split[1])
            self.month =int(split[0])
            self.year = int(split[2])
        except:
            self.error=True
    def __repr__(self):
        return f"{self.month}/{self.day}/{self.year}"
class Dates:
    def __int__(self,name:str,value:str):
        self.name =name
        self.error = False
        split = value.split(" ")
        try:
            for sp
            self.day = int(split[1])
            self.month =int(split[0])
            self.year = int(split[2])
        except:
            self.error=True

class Team:
    def __init__(self, fullName, shortName, division, practiceDays, homeFacility,
                 alternateFacility, noPlayDates, noMatchDays, homeMatchPCT, startDate):
        self.fullName = Prop("Full Name",fullName)
        self.shortName = Prop("Short Name",shortName)
        self.division = Prop("Division",division)
        self.practiceDays = Prop("Practice Days", practiceDays)
        self.homeFacility = Prop("Home Facility",homeFacility)
        self.alternateFacility = Prop("Alternate Facility",alternateFacility)
        self.noPlayDates = Prop("No Play Dates",noPlayDates)
        self.noMatchDays = Prop("No Match Days",noMatchDays)
        self.homeMatchPCT = Prop("Home Match %",homeMatchPCT)
        self.startDate = Prop("Start Date",startDate)
        self.properties = [self.fullName,self.shortName,self.division,self.practiceDays,self.homeFacility,self.alternateFacility,self.noPlayDates,self.noMatchDays,self.homeMatchPCT,self.startDate]
    # def __str__(self):
    #     s = ""
    #     for prop in self.properties:
    #         s+=f"{prop.name}: {prop}<br>"
    #     return s
    def summary(self):
        print(self.shortName, self.division)


properties = ["Team Name", "Abbreviated Name", "Division", "Practice Days", "Home Facility",
              "Alternate Facility", "No Play Dates", "No Match Days", "Home Match %", "Start Date"]

# team0 = Team("Greenwich", "GHS", "FCIAC","Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31", "12/31", "50", "12/1")
