import ConvenientFunctions as cf
from firebase_admin import firestore

# likedByの配列の長さでソートする
def get_liked_by_length(doc):
    liked_by = doc.to_dict().get("likedBy")
    return len(liked_by) if liked_by else 0

def main():
    flavor = cf.getFlavor()
    cf.initializeFirebase(flavor)
    db = firestore.client()
    # Celebritiesコレクションの全ドキュメントを取得
    celebrities_ref = db.collection("celebrities")
    celebrities_docs = celebrities_ref.get()
    sorted_celebrities = sorted(celebrities_docs, key=lambda doc: len(doc.to_dict().get("likedBy", [])), reverse=True)
    # 結果を出力
    for doc in sorted_celebrities:
        name = doc.to_dict().get("name", "")
        liked_by_length = get_liked_by_length(doc)
        print(f"likedBy Length: {liked_by_length}, Name: {name}")

if __name__ == '__main__':
    main()