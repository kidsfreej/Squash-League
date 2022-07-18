import PySimpleGUI as sg


# TODO Web page (flask) as input/UI
# TODO

# test
class Team:
    def __init__(self, fullName, shortName, division, practiceDays, homeFacility,
                 alternateFacility, noPlayDates, noMatchDays, homeMatchPCT, startDate):
        self.fullName = fullName
        self.shortName = shortName
        self.division = division
        self.practiceDays = practiceDays
        self.homeFacility = homeFacility
        self.alternateFacility = alternateFacility
        self.noPlayDates = noPlayDates
        self.noMatchDays = noMatchDays
        self.homeMatchPCT = homeMatchPCT
        self.startDate = startDate

    def summary(self):
        print(self.shortName, self.division)


properties = ["Team Name", "Abbreviated Name", "Division", "Practice Days", "Home Facility",
              "Alternate Facility", "No Play Dates", "No Match Days", "Home Match %", "Start Date"]

# team0 = Team("Greenwich", "GHS", "FCIAC","Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31", "12/31", "50", "12/1")
