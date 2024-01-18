import pyperclip

def loop(selectedText) -> list[str]:
    tokenList = []
    for i in range(len(selectedText)):
        token = selectedText[0:i + 1]
        if token not in tokenList:
            tokenList.append(token)
    return tokenList

def do():
    tokenList = []
    print('文字列を入力:')
    text = input()
    tokenList.extend(loop(text))
    tokenList.extend(loop(text.upper()))
    tokenList.extend(loop(text.lower()))
    tokenList.extend(loop(text.capitalize()))

    tokenList.extend(loop(text.replace(' ', '')))
    tokenList.extend(loop(text.replace(' ', '').upper()))
    tokenList.extend(loop(text.replace(' ', '').lower()))
    tokenList.extend(loop(text.replace(' ', '').capitalize()))
    
    tokenList = list(dict.fromkeys(tokenList))
    tokenMapText = "[\n"
    for i in range(len(tokenList)):
        tokenMapText = tokenMapText + f'  "{tokenList[i]}"'
        if i != len(tokenList) - 1:
            tokenMapText = tokenMapText + ','
        tokenMapText = tokenMapText + '\n'
    tokenMapText = tokenMapText + ']'
    print(tokenMapText)
    print('firestoreの"tokenMap"フィールに上記のマップを追加してください。')
    print('クリップボードにコピーされました。')
    pyperclip.copy(tokenMapText)

def main():
    do()

if __name__ == '__main__':
    main()