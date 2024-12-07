import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('path/to/your/firebase_credentials.json')  # Update with your path
firebase_admin.initialize_app(cred)

db = firestore.client()
