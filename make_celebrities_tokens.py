import pyperclip

def loop(selected_text) -> list[str]:
    token_list = []
    for i in range(len(selected_text)):
        token = selected_text[0:i + 1]
        if token not in token_list:
            token_list.append(token)
    return token_list

def do():
    token_list = []
    print('文字列を入力:')
    text = input()
    token_list.extend(loop(text))
    token_list.extend(loop(text.upper()))
    token_list.extend(loop(text.lower()))
    token_list.extend(loop(text.capitalize()))

    token_list.extend(loop(text.replace(' ', '')))
    token_list.extend(loop(text.replace(' ', '').upper()))
    token_list.extend(loop(text.replace(' ', '').lower()))
    token_list.extend(loop(text.replace(' ', '').capitalize()))
    
    token_list = list(dict.fromkeys(token_list))
    token_map_text = "[\n"
    for i in range(len(token_list)):
        token_map_text = token_map_text + f'  "{token_list[i]}"'
        if i != len(token_list) - 1:
            token_map_text = token_map_text + ','
        token_map_text = token_map_text + '\n'
    token_map_text = token_map_text + ']'
    print(token_map_text)
    print('firestoreの"tokenMap"フィールに上記のマップを追加してください。')
    print('クリップボードにコピーされました。')
    pyperclip.copy(token_map_text)

def main():
    do()

if __name__ == '__main__':
    main()