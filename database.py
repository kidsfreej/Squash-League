import sqlite3
from TeamData import Team


class Database:
    def __init__(self):
        # Set up connection to dbs
        self.con = sqlite3.connect('data.db',check_same_thread=False)
        self.cur = self.con.cursor()
        try:
            self.cur.execute('''CREATE TABLE teams
                      (FullName text, AbbvName text, Division text, PracticeDays text, HomeFacility text, AlternateFacility text, 
                      NoPlayDates text, NoMatchDays text, HomeMatchPCT text, StartDate text)''')
        except:
            pass
        self.save()

    def save(self):
        self.con.commit()
        #self.con.close()

    def clear_table(self):
        # Clear table from memory
        self.cur.execute("DROP TABLE teams")
        self.save()

    def add_team(self, team):
        self.cur.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (team.fullName.__repr__(), team.shortName.__repr__(), team.division.__repr__(),
                          team.practiceDays.__repr__(), team.homeFacility.__repr__(), team.alternateFacility.__repr__(),
                          team.noPlayDates.__repr__(), team.noMatchDays.__repr__(), team.homeMatchPCT.__repr__(),
                          team.startDate.__repr__()))
        # Save (commit) the changes
        self.save()

    def remove_team(self, teamName):
        delete = """DELETE FROM teams WHERE FullName = ?"""
        self.cur.execute(delete, (teamName,))
        self.save()

    def print_all(self):
        print("Teams:")
        for row in self.cur.execute('SELECT * FROM teams'):
            print(row)


# FullName, AbbvName, Division , PracticeDays , HomeFacility , AlternateFacility ,NoPlayDates , NoMatchDays , HomeMatchPCT , StartDate
#team0 = Team("Greenwich", "GHS", "FCIAC", "Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31",
            # "12/31", "50", "12/1")