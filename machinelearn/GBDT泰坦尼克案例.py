"""
    Boosting 思想：GBDT（梯度提升树）
    GBDT：通过拟合负梯度 获取强学习器
        1.采取所有数据的均值作为第一个弱学习器的预测值
        2.目标值 - 预测值 = 负梯度（残差） 再讲该值作为第二个弱学习器的目标值
        3.对于第一个学习器，依次计算每个分隔点的 最小平方和 找到最佳分割点
"""
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score

# 数据导入
data = pd.read_csv("./data/train.csv")
# 数据预处理
x = data[["Pclass", "Age", "Sex"]].copy()
y = data["Survived"]
x["Age"] = x["Age"].fillna(x["Age"].mean())
x = pd.get_dummies(x)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25)
# 模型训练
param = {'n_estimators': [10, 30, 80, 50, 40, 110],
         'learning_rate':[0.1, 0.4, 0.9, 0.15, 0.5, 0.7],
         'max_depth': [1, 2, 3, 4, 8, 7]}
estimator1 = DecisionTreeClassifier()
estimator2 = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3)
estimator3 = GradientBoostingClassifier()
estimator4 = GridSearchCV(estimator3, param, cv=2)
estimator1.fit(x_train, y_train)
estimator2.fit(x_train, y_train)
estimator3.fit(x_train, y_train)
estimator4.fit(x_train, y_train)
# 模型预测
y_predict1 = estimator1.predict(x_test)
y_predict2 = estimator2.predict(x_test)
y_predict3 = estimator3.predict(x_test)
y_predict4 = estimator4.predict(x_test)
print(f'单个决策树的预测值：\n {y_predict1}')
print(f'GBDT决策树的预测值：\n {y_predict2}')
print(f'无参的GBDT的决策树预测值：\n {y_predict3}')
print(f'网格搜索预测值：\n {y_predict4}')
# 模型评估
print(f'单个决策树的准确率：{accuracy_score(y_test, y_predict1)}')
print(f'GBDT决策树的准确率：{accuracy_score(y_test, y_predict2)}')
print(f'无参的GBDT决策树准确率：{accuracy_score(y_test, y_predict3)}')
print(f'网格搜索的准确率：{accuracy_score(y_test, y_predict4)}')
print(classification_report(y_test, y_predict1))
print(classification_report(y_test, y_predict2))
print(classification_report(y_test, y_predict3))
print(classification_report(y_test, y_predict4))
print(f'单个决策树特征重要性：{estimator1.feature_importances_}')
print(f'GBDT决策树特征重要性：{estimator2.feature_importances_}')
print(f'无参的GBDT决策树特征重要性：{estimator3.feature_importances_}')
print(f'网格搜索决策树特征重要性：{estimator4.best_estimator_.feature_importances_}')