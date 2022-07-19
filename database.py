import sqlite3
from TeamData import Team

#Set up connection to db

con = sqlite3.connect('data.db')

cur = con.cursor()

#Clear table from memory
cur.execute("DROP TABLE teams")
# Create table


team0 = Team("Greenwich", "GHS", "FCIAC","Monday, Wednesday, Friday", "Chelsea Piers", "Chelsea Piers", "12/31", "12/31", "50", "12/1")

#team0.fullName, team0.shortName, team0.division,  team0.practiceDays, team0.homeFacility, team0.alternateFacility, team0.noPlayDates, team0.noMatchDays, team0.homeMatchPCT, team0.startDate


cur.execute('''CREATE TABLE teams
              (FullName text, AbbvName text, Division text, PracticeDays text, HomeFacility text, AlternateFacility text, 
              NoPlayDates text, NoMatchDays text, HomeMatchPCT text, StartDate text)''')

# Insert a row of data
cur.execute("INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (team0.fullName.__repr__(), team0.shortName.__repr__(), team0.division.__repr__(),
             team0.practiceDays.__repr__(), team0.homeFacility.__repr__(), team0.alternateFacility.__repr__(),
             team0.noPlayDates.__repr__(), team0.noMatchDays.__repr__(), team0.homeMatchPCT.__repr__(), team0.startDate.__repr__()))

# Save (commit) the changes
con.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.

for row in cur.execute('SELECT * FROM teams'):
    print(row)

con.close()