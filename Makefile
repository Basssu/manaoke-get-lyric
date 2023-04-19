videoIds = -L7eMf6Yf84

.PHONY: all

# allターゲットはすべてのビデオIDに対して実行する
all: $(foreach id,$(videoIds),$(id))

# 各ビデオIDに対してスクリプトを実行するルールを定義する
$(videoIds):
	python captionToTxt.py $@
	node hangulToKatakana.js $@
	python txtToJson.py $@
	python toFirebase.py $@ stg
#↑stgをprodに書き換えて本番環境にアップロード