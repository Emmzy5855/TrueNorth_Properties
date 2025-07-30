import mysql.connector

mydb = mysql.connector.Connect(
    host="maglev.proxy.rlwy.net",
    user="root",
    passwd="WWWohlVZHMSYgmmikzqgTWGXMUEpttYH",
    database="railway",
    port=55641  
)

my_cursor = mydb.cursor()

#my_cursor.execute("CREATE DATABASE railway")

my_cursor.execute("SHOW DATABASES")

for db in my_cursor:
    print(db)