import pymongo
from .AppConfig import config

def get_db_instance():
    connection_uri = config.database_url
    client = pymongo.MongoClient(connection_uri)
    return client.get_database('mercorChatDb')
