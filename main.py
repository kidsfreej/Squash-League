import PySimpleGUI as sg


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

teamProperties = []

layout = [
    [[sg.Text("Input " + properties[i]), sg.Input() for i in range(len(properties))], sg.Button('Enter')
for row in range(4)]
]
# Create the window
window = sg.Window('Window Title', layout)  # Part 3 - Window Defintion

# Display and interact with the Window
event, values = window.read()  # Part 4 - Event loop or Window.read call

# Do something with the information gathered
values = list(values.values())
print('Storing...', values[0])
teamProperties.append(values[0])

# Finish up by removing from the screen
window.close()  # Part 5 - Close the Window

# team0 = Team("Greenwich", "GHS", "FCIAC","Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31", "12/31", "50", "12/1")
team1 = Team(teamProperties[0], teamProperties[1], teamProperties[2], teamProperties[3], teamProperties[4],
             teamProperties[5],
             teamProperties[6], teamProperties[7], teamProperties[8], teamProperties[9])

# team0.summary()
team1.summary()
