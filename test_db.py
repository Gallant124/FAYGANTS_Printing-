import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Faygants@2026",
    database="faygants_db"
)

if connection.is_connected():
    print("Connected to MySQL successfully!")

connection.close()