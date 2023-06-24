import datetime

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