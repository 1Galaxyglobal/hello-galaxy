"""
    集成学习 Bagging思想 随机森林
集成学习： 把多个弱学习器（基学习器）组合成一个强学习器的过程
思想： Bagging：（随机森林）——>每个弱学习器都是CART树 并且是二叉树
            1.有放回的随机取样
            2.平权投票
            3.可以并行执行
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier  # 随机森林算法分类器
from sklearn.tree import DecisionTreeClassifier     # 决策树
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV    # 网格搜索

# 以泰坦尼克号数据集为例
# 1.数据导入
data = pd.read_csv("./data/train.csv")
# data.info()
x = data[["Pclass", "Age", "Sex"]].copy()
y = data["Survived"]
# print(x)
# 2.数据的预处理
# 2.1 空值处理 用age列的平均值填充age列的缺失值
x["Age"].fillna(x["Age"].mean())
# 2.2热编码
x = pd.get_dummies(x)
# 2.3数据集切割
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25)
# 3.模型训练
estimator1 = DecisionTreeClassifier()
estimator2 = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split=2)
estimator1.fit(x_train, y_train)
estimator2.fit(x_train, y_train)
# 4.模型预测
y_predict1 = estimator1.predict(x_test)
y_predict2 = estimator2.predict(x_test)
print(y_predict1)
print(y_predict2)
# 5.模型评估
print(f'准确率1：{estimator1.score(x_test, y_test)}')
print(f'准确率2：{estimator2.score(x_test, y_test)}')

# 随机森林算法——>网格搜索
estimator3 = RandomForestClassifier()
param_grid = {"n_estimators": [10, 20, 30, 40, 50, 60, 70],'max_depth': [1, 2, 3, 4, 5, 6, 7],}
gs_estimator = GridSearchCV(estimator3, param_grid, cv=2)
gs_estimator.fit(x_train, y_train)
y_predict3 = gs_estimator.predict(x_test)
print(f'预测值3：{y_predict3}')
print(f'准确率3：{gs_estimator.score(x_test, y_test)}')
print(f'最佳参数：{gs_estimator.best_params_}')

