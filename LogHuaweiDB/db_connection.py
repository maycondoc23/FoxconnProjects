import mysql.connector
# server=10.8.28.68;database=dbfalconcore;uid=falconcore;pwd=f@lc0nc0r3;sslmode=none
def connect_db():
    return mysql.connector.connect(
        host="10.8.28.68",  
        user="falconcore",        
        password="f@lc0nc0r3",  
        database="dbfalconcore"  
    )