class AppConfig:
    app_name: str = "Mercor Chat Server V1"
    debug: bool = False
    database_url: str = "mongodb+srv://kunalsan:kunalsan@cluster.izyefmw.mongodb.net/?retryWrites=true&w=majority"
    origins = [
    "http://localhost:3000",  # React app address
    ]   

config = AppConfig()