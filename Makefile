# videoIds = 6ZUIwj3FgUY MVjQIQGqNFM pG6iaOMV46I EDnwWcFpObo 5eh6Vj_vVg4 aPPq_FJC-BU dK7a9rDgU3g T6YVgEpRU6Q 3TQd2ahq6oU L7spCJxloLY likYKQXBLbw 9trNIRzbPMc vfUAckewh_8 _ZAgIHmHLdc tUCT82t1Y8Q pSUydWEqKwE
videoIds = 8-yLpmM5yyI 9F6s04gbQPw NN2N69hH12g aYYAzHZFnZg 4GbLmfU5VxE XBkxP4Zb3ZM xgDMfMt7kDs fEGAfDeGYhk ouDzbBO8ctA

.PHONY: all

# allターゲットはすべてのビデオIDに対して実行する
all: $(foreach id,$(videoIds),$(id))

# 各ビデオIDに対してスクリプトを実行するルールを定義する
$(videoIds):
	python captionToTxt.py $@
	node hangulToKatakana.js $@
	python txtToJson.py $@
	python toFirebase.py $@ prod
#↑stgをprodに書き換えて本番環境にアップロード