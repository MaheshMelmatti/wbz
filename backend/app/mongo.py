from pymongo import MongoClient

MONGO_URI = "mongodb+srv://myuser:mypassword123@cluster0.pqllad8.mongodb.net/signal_analyzer?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["signal_analyzer"]

scans_collection = db["scans"]
