import html

# TODO Web page (flask) as input/UI
# TODO
properties = ["Team Name", "Abbreviated Name", "Division", "Practice Days", "Home Facility",
              "Alternate Facility", "No Play Dates", "No Match Days", "Home Match %", "Start Date"]
# test
class Prop:
    def __init__(self,name:str,value):
        self.name = name
        self.value = value.strip()
        self.error = False
    def __repr__(self):
        return repr(self.value)
class Dates:
    def __init__(self,name:str,value:str):
        self.name =name
        self.error = False
        split = value.strip().split(",")
        self.dates = []
        try:
            for sp in split:
                self.dates.append(Dates(name,sp.strip()))
        except:
            self.error=True
            self.value = value
class Number:
    def __init__(self,name:str,value:str):
        self.error = False
        self.name = name
        try:
            self.value = float(value.strip())
        except:
            self.error =True
            self.value = value
class Team:
    def __init__(self, fullName, shortName, division, practiceDays, homeFacility,
                 alternateFacility, noPlayDates, noMatchDays, homeMatchPCT, startDate):
        self.fullName = Prop("Full Name",fullName)
        self.shortName = Prop("Short Name",shortName)
        self.division = Prop("Division",division)
        self.practiceDays = Dates("Practice Days", practiceDays)
        self.homeFacility = Prop("Home Facility",homeFacility)
        self.alternateFacility = Prop("Alternate Facility",alternateFacility)
        self.noPlayDates = Dates("No Play Dates",noPlayDates)
        self.noMatchDays = Dates("No Match Days",noMatchDays)
        self.homeMatchPCT = Number("Home Match %",homeMatchPCT)
        self.startDate = Dates("Start Date",startDate)
        self.properties = [self.fullName,self.shortName,self.division,self.practiceDays,self.homeFacility,self.alternateFacility,self.noPlayDates,self.noMatchDays,self.homeMatchPCT,self.startDate]
        errors = []
        for prop in self.properties:
            if prop.error:
                m = f"{prop.name}: "
                if type(prop)==Number:
                    m+=f"Make sure to enter a number (no other symbols). You entered '{prop.value}'."
                elif type(prop)==Date:
                    m+=f"Make sure to enter a date (mm/dd/yy). You entered '{prop.value}'"
                elif type(prop)==Dates:
                    k = 'and'.join([f"'{d}'" for d in prop.value.split()])
                    m+=f"Make sre you enter common seperated date(s). You entered {k}"
                else:
                    raise NotImplementedError("oopsies")
                errors.append(m)
        self.errors = errors
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
