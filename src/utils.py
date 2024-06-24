from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_cosine_similarity(text1, text2):
    # 创建一个TfidfVectorizer对象
    vectorizer = TfidfVectorizer()
    
    # 将文本转换为TF-IDF矩阵
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    
    # 计算余弦相似度
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
    return cosine_sim[0][0]


def is_similar(text1, text2):
    score = calculate_cosine_similarity(text1=text1, text2=text2)
    return score > 0.7