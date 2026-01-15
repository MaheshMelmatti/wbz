from app.mongo import db

print("Connected ✅")
print("Collections:", db.list_collection_names())
