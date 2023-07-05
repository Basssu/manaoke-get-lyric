import datetime
from firebase_admin import credentials

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