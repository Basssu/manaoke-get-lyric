import pyperclip
tokenList = []

def loop(selectedText):
    for i in range(len(selectedText)):
        token = selectedText[0:i + 1]
        if token not in tokenList:
            tokenList.append(token)

print('文字列を入力:')
text = input()
loop(text)
loop(text.upper())
loop(text.lower())
loop(text.capitalize())

loop(text.replace(' ', ''))
loop(text.replace(' ', '').upper())
loop(text.replace(' ', '').lower())
loop(text.replace(' ', '').capitalize())

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