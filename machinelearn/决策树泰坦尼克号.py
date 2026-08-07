"""
    CART树
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report
from sklearn.tree import export_graphviz
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

# 加载数据
data = pd.read_csv('./data/train.csv')
# print(data.head())
# data.info()

# 数据的预处理
x = data[['Pclass', 'Age', 'Sex']]
y = data['Survived']
x = x.copy()
x['Age'] = x['Age'].fillna(x['Age'].mean()) # 将年龄的空值填充成平均值
# x.info()
x = pd.get_dummies(x, columns=['Sex'])
# x.info()
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25)

# 模型训练
estimator = DecisionTreeClassifier(max_depth=10, criterion='entropy') # 最多十层
estimator.fit(x_train, y_train)
# 模型预测
y_pre = estimator.predict(x_test)
print('预测结果是：\n ', estimator.predict(x_test))
print('预测结果是：', estimator.score(x_test, y_test))
print('预测结果是：\n ', classification_report(y_test, estimator.predict(x_test)))
# 可视化
plt.figure(figsize=(10, 10))
plot_tree(estimator, filled=True, max_depth=10)
plt.savefig('./data/tree.png')
plt.show()
# 模型评估