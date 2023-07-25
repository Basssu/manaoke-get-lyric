import datetime
from firebase_admin import credentials
import re
import firebase_admin

def formatTime(time: float) -> str:
    return (datetime.timedelta(seconds=time) + datetime.datetime(1900,1,1)).strftime('%H:%M:%S,%f')[:-3]

def answeredYes(question: str) -> bool:
    while True:
        print(f'{question}(y/n)')
        answer = input()
        if answer == 'y':
            return True
        elif answer == 'n':
            return False
        else:
            print('yかnで答えてください')

def inputText(question: str) -> str:
    print(question)
    text = input()
    return text

def initializeFirebase(flavor: str):
    cred = firebaseCreds(flavor)
    domain = firebaseDomain(flavor)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'storageBucket': domain
        })
    return cred, domain

def firebaseCreds(flavor: str):
    if flavor == "prod":
        return credentials.Certificate("../firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    else:
        return credentials.Certificate("../firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")

def firebaseDomain(flavor: str):
    if flavor == "prod":
        return "manaoke-8c082.appspot.com"
    else:
        return "manaoke-stg.appspot.com"
    
def removeBrackets(text: str, brackets: str) -> str:
    pattern = re.escape(brackets[0]) + r'[^\[{}\]()]*' + re.escape(brackets[1])
    result = re.sub(pattern, '', text)
    return result

def getFlavor() -> str:
    return 'prod' if answeredYes('flavorはどっち？(y = prod, n = stg)') else 'stg'