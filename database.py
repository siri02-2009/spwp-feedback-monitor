import mysql.connector


def get_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysqlpassword",
        database="feedback_system"
    )

    return connection
