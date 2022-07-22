import sqlite3
from TeamData import Team, Facility, Prop


class Database:
    def __init__(self):
        # Set up connection to dbs
        self.con = sqlite3.connect('data.db', check_same_thread=False)
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
        # self.con.close()

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

    def get_teams(self):
        teams = {}
        for row in self.cur.execute('SELECT * FROM teams'):
            teams[row[0]] = Team(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
        return teams

class facilityDatabase:
    def __init__(self):
        # Set up connection to dbs
        self.con = sqlite3.connect('facilities.db', check_same_thread=False)
        self.cur = self.con.cursor()
        try:
            self.cur.execute('''CREATE TABLE facilities
                                  (Year text, FullName text, AbbvName text, StartDate text, EndDate text)''')
        except:
            pass
        self.save()

    def save(self):
        self.con.commit()
        # self.con.close()

    def clear_table(self):
        # Clear table from memory
        self.cur.execute("DROP TABLE facilities")
        self.save()

    def add_facility(self, Facility):
        self.cur.execute("INSERT INTO facilities VALUES (?, ?, ?, ?, ?)",
                         (Facility.year.__repr__(), Facility.fullName.__repr__(), Facility.shortName.__repr__(),
                          Facility.start.__repr__(), Facility.end.__repr__()))
        # Save (commit) the changes
        self.save()

    def remove_facility(self, facilityName):
        delete = """DELETE FROM facilities WHERE FullName = ?"""
        self.cur.execute(delete, (facilityName,))
        self.save()

    def print_all(self):
        print("Facilities:")
        for row in self.cur.execute('SELECT * FROM facilities'):
            print(row)

    # DO THE REST OF THESE METHODS BELOW
    def get_facilities(self):
        facilities = {}
        for row in self.cur.execute('SELECT * FROM facilities'):
            facilities[row[1]] = Facility(row[0], row[1], row[2], row[3], row[4])
        return facilities

# FullName, AbbvName, Division , PracticeDays , HomeFacility , AlternateFacility ,NoPlayDates , NoMatchDays , HomeMatchPCT , StartDate
team0 = Team("Greenwich", "GHS", "FCIAC", "Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31/22",
             "12/31/22", "50", "12/1/22")
facility0 = Facility("2022", "Fairfield County", "FCIAC", "12/31/2022", "2/14/2023")

#testDB = Database()
# testDB.add_team(team0)
# testDB.remove_team("Greenwich")
#testDB.print_all()
#print(testDB.get_teams())

facilityDB = facilityDatabase()
#facilityDB.remove_facility("Fairfield County")
#facilityDB.add_facility(facility0)
print(facilityDB.get_facilities())
facilityDB.print_all()