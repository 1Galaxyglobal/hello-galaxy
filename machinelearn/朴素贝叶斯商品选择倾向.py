"""
通过朴素贝叶斯算法实现对商品的好评差评分析
    贝叶斯：仅仅依赖概率就可以进行分类的算法
    朴素贝叶斯：不考虑先后顺序 不考虑特征之间的关联性 即认为每个特征之间的关系是相互独立的
    P(AB) = P(A) * P(B) = P(A) * P(B|A)
"""
import jieba                    # 分词包
import numpy as np              # 数学计算包
import pandas as pd             # 数据处理包
import matplotlib.pyplot as plt # 画图包
from sklearn.feature_extraction.text import CountVectorizer # 词频统计包  把评论内容转成词频矩阵
from sklearn.naive_bayes import MultinomialNB               # 朴素贝叶斯
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score  # 打印详细的分类报告
# 1. 读取数据
data = pd.read_csv('./data/书籍评价.csv', encoding='utf-8-sig')
# 2. 构建标签（正面=1，负面=0）
data['labels'] = np.where(data['评价'] == '正面', 1, 0)
labels = data['labels']
# 3. 加载停用词列表
with open('./data/stopwords.txt', 'r', encoding='utf-8') as f:
    stopwords = f.read().splitlines()
    stopwords = set(stopwords) # 去重，提高查询效率
print(f"\n停用词数量: {len(stopwords)}")
# 4. 对评论内容进行分词并去除停用词
def process_text(text):
    """对单条文本进行分词并去除停用词"""
    words = jieba.lcut(text)
    # 去除停用词和空格
    words = [word for word in words if word not in stopwords and word.strip()]
    return ' '.join(words)  # 用空格连接，CountVectorizer默认按空格分词
# 处理所有评论
processed_comments = [process_text(line) for line in data['内容']]
print(f"\n处理后的评论示例（前2条）:")
for i, comment in enumerate(processed_comments[:2]):
    print(f"  评论{i+1}: {comment}")
# 5. 特征提取：将文本转换为词频矩阵
transfer = CountVectorizer()
transfer.fit(processed_comments)
features = transfer.transform(processed_comments).toarray()
print(f"\n特征矩阵形状: {features.shape}")
print(f"词汇表大小: {len(transfer.get_feature_names_out())}")
print(f"前20个特征词: {transfer.get_feature_names_out()[:20]}")
# 6. 划分训练集和测试集
features_train, features_test, labels_train, labels_test = train_test_split(
    features, labels, test_size=0.2, random_state=20
)
print(f"\n训练集样本数: {features_train.shape[0]}")
print(f"测试集样本数: {features_test.shape[0]}")
# 7. 训练朴素贝叶斯模型
estimator = MultinomialNB()
estimator.fit(features_train, labels_train)
# 8. 预测
predict = estimator.predict(features_test)
print("\n预测结果:")
print(predict)
# 9. 评估
print(f"\n准确率: {accuracy_score(labels_test, predict)}")
print("\n分类报告:")
print(classification_report(labels_test, predict, target_names=['负面', '正面']))
print("混淆矩阵:")
print(confusion_matrix(labels_test, predict))
# 10. 测试自定义评论
print("\n" + "="*50)
print("测试自定义评论:")
test_comments = [
    "这本书写得非常好，内容详实，值得推荐",
    "质量很差，印刷模糊，完全不值得购买",
    "一般般吧，没什么特别的感觉"
]

for comment in test_comments:
    processed = process_text(comment)
    features_test = transfer.transform([processed])
    prediction = estimator.predict(features_test)[0]
    proba = estimator.predict_proba(features_test)[0]
    sentiment = "正面" if prediction == 1 else "负面"
    print(f"评论: {comment}")
    print(f"  情感: {sentiment} (置信度: {proba.max():.2%})")