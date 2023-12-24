#connecting mysql
import pymysql

config = {
    'host': '35.224.61.48',
    'user': 'trial_user',
    'password': 'trial_user_12345#',
    'database': 'MERCOR_TRIAL_SCHEMA',
    'port':3306
}
def get_connection():
    connection = pymysql.connect(**config) 
    return connection 