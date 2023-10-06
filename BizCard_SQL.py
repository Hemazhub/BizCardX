import mysql.connector as sql

# Connecting to MySQL Workbench
mydb = sql.connect(host='localhost',
                   user = 'root',
                   password = 'Mysql@2023',
                   database = 'BizCard')

cursor = mydb.cursor()

#Creating a table
cursor.execute('''CREATE TABLE IF NOT EXISTS bizcard_data
                    (
                    company_name Varchar(255),
                    card_holder_name Varchar(255),
                    Designation Varchar(255),
                    Mob_num Varchar(255),
                    email TEXT,
                    website TEXT,
                    Area TEXT,
                    City Varchar(255),
                    State Varchar(255),
                    PINCODE Varchar(255)
                    )''')