import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
firebase_admin.initialize_app(cred)

db= firestore.client()

db.collection('prsons').add({'name':'kobayashi','age':40,'occupation':'programmer'})