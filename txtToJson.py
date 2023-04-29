import json
import MeCab
import mecab_ko_dic
import requests
import sys
import pprint as goodPrint
from konlpy.tag import Okt
from konlpy.utils import pprint

def should_translate(word_info):
    pos = word_info[1]['pos']
    # 名詞、動詞、形容詞、副詞は翻訳する
    if pos.startswith('N') or pos.startswith('V') or pos.startswith('M') or pos.startswith('VA'):
        return True
    # 助詞が合成されている名詞は原形で翻訳する
    if pos == 'NNG+JKO' or pos == 'NNP+JKO' or pos == 'NNB+JX':
        return True
    return False

def translate(input):
    api_url = "https://script.google.com/macros/s/AKfycbxD-HCVUlVhyjlf7pdfsYtKW_png6FqY1wO_Pf2KurOE0rEKVo3SZXHgjwx2OLDAVzW/exec"
    params = {
        'text': input,
        'lang_from': 'ko',
        'lang_to'  : 'ja'
    }
    r_post = requests.post(api_url, data=params)
    return r_post.json()["result"]

def analysis(text):
    okt = Okt()
    tagger = MeCab.Tagger(mecab_ko_dic.MECAB_ARGS)
    lines = tagger.parse(text)
    result = []
    for line in lines.split("\n"):
        split_line = line.split("\t")
        word = split_line[0]
        if word == ' ' or word == u'\xa0':
            continue
        if word == "EOS":
            break
        features = split_line[1].split(",")
        pos = features[0]
        start_pos = features[5]
        end_pos = features[6]
        expression = features[7] if len(features) > 7 else None
        result.append([word, {"pos": pos, "start_pos": start_pos, "end_pos": end_pos, "expression": expression}])
    for i in range(len(result)):
        result[i][1]["stem"] = okt.pos(result[i][0], norm=False, stem=True)[0][0]
        result[i][1]["stem_pos"] = okt.pos(result[i][0], norm=False, stem=True)[0][1]

        #https://krdict.korean.go.kr/jpn/mainAction?nation=jpn を使うことにしたので翻訳は一旦なし

        # if should_translate(result[i]):
        #     if "+" in result[i][1]["pos"] and result[i][1]["pos"][0] == "N":
        #         result[i][1]["translation"] = translate(result[i][1]["stem"])
        #     else:
        #         result[i][1]["translation"] = translate(result[i][1]["stem"])
        # else:
        #     result[i][1]["translation"] = translate(result[i][1]["stem"])
    # print(result)
    return result

# コマンドライン引数からパラメータを受け取る
params = sys.argv[1:]
video_id = params[0]

with open(f'videos/{video_id}/subtitle_all.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    lyrics = []
    for i in range(0, len(lines), 6):
        print(f'{str(i)}/{str(len(lines))}')
        try:
            time = lines[i+1].strip()
            full_meaning = lines[i+3].strip()
            lyrics_list = lines[i+2].strip().split()
            ruby_list = lines[i+4].strip().split()
            lycicOneLins = lines[i+2]
            analysisList = analysis(lycicOneLins)
            if len(lyrics_list) != len(ruby_list):
                raise ValueError('lyrics and ruby are not aligned')
            detail = []
            for j in range(len(lyrics_list)):
                words = []
                for k in range(len(analysisList)):
                    if analysisList[k][0] in lyrics_list[j]:
                        words.append(analysisList[k])
                # print("a:", lyrics_list[j])
                # print("b:", words)
                detail.append({'actualLyric': lyrics_list[j], 'analysis': words, 'ruby': ruby_list[j]})
            # detail = [{'actualLyric': lyric, 'analysis': analysis(lyric), 'ruby': ruby} for lyric, ruby in zip(lyrics_list, ruby_list)]
            lyrics.append({'time': time, 'fullMeaning': full_meaning, 'detail': detail})
        except IndexError:
            break
        except ValueError as e:
            print(f"Error in line {i+1}: {e}")
            break

with open(f'videos/{video_id}/allData.json', "w") as f:
    json.dump(lyrics, f, indent=4, ensure_ascii=False)