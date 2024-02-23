import datetime
from firebase_admin import credentials
import re
import firebase_admin

def format_time(time: float) -> str:
    return (datetime.timedelta(seconds=time) + datetime.datetime(1900,1,1)).strftime('%H:%M:%S,%f')[:-3]

def answered_yes(question: str) -> bool:
    while True:
        print(f'{question}(y/n)')
        answer = input()
        if answer == 'y':
            return True
        elif answer == 'n':
            return False
        else:
            print('yかnで答えてください')

def input_text(question: str) -> str:
    print(question)
    text = input()
    return text

def initialize_firebase(flavor: str):
    cred = firebase_creds(flavor)
    domain = firebase_domain(flavor)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'storageBucket': domain
        })
    return cred, domain

def firebase_creds(flavor: str):
    if flavor == "prod":
        return credentials.Certificate("../firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    else:
        return credentials.Certificate("../firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")

def firebase_domain(flavor: str):
    if flavor == "prod":
        return "manaoke-8c082.appspot.com"
    else:
        return "manaoke-stg.appspot.com"
    
def remove_brackets(text: str, brackets: str) -> str:
    pattern = re.escape(brackets[0]) + r'[^\[{}\]()]*' + re.escape(brackets[1])
    result = re.sub(pattern, '', text)
    return result

def get_flavor() -> str:
    return 'prod' if answered_yes('flavorはどっち？(y = prod, n = stg)') else 'stg'