"""
Boosting：
            1.每次投票使用全部的样本
            2.加权投票 ——>预测正确 权重减小  ||  预测错误 权重增加
            3.只能串行执行
AdaBoost:
            1.使用全部样本，通过决策树（CART树）（二叉树）（第一个弱分类器）训练
                加权投票 ——>预测正确 权重减小  ||  预测错误 权重增加
            2.把第一个弱分类器处理的结果给第二个分类器进行训练
            以此类推 串行执行

"""
import pandas as pd
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
"""
#   Column                Non-Null Count  Dtype  
---  ------                --------------  -----  
 0   Class_label           178 non-null    int64  
 1   Alcohol               178 non-null    float64
 2   Malic_acid            178 non-null    float64
 3   Ash                   178 non-null    float64
 4   Alcalinity_of_ash     178 non-null    float64
 5   Magnesium             178 non-null    float64
 6   Total_phenols         178 non-null    float64
 7   Flavanoids            178 non-null    float64
 8   Nonflavanoid_phenols  178 non-null    float64
 9   Proanthocyanins       178 non-null    float64
 10  Color_intensity       178 non-null    float64
 11  Hue                   178 non-null    float64
 12  OD280_OD315           178 non-null    float64
 13  Proline               178 non-null    float64
"""
# 数据导入
data = pd.read_csv('../data/wine.csv')
# data.info()
# print(data['Class_label'].unique())     # [1 2 3] 葡萄酒类型有3种 但决策树只是二叉树
# 数据预处理
# 从标签列中过滤掉 1 类型 剩下2 3 类型
data = data[data['Class_label'] != 1]
x = data[['Alcohol','Hue']]
y = data['Class_label']
# print(x[:5])
# print(y[:5])
le = LabelEncoder()
y = le.fit_transform(y) # 标签列转换成数值列
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y, random_state=22)
# 模型训练
estimator1 = DecisionTreeClassifier(max_depth=3) # 单一决策树充当弱分类器
estimator2 = AdaBoostClassifier(estimator=estimator1, n_estimators=50, learning_rate=0.1) # 集成分类器AdaBoost CART树
                                # 参1：弱分类器（决策树）参2：n_estimators: 集成分类器的数量 参3：学习率
estimator1.fit(x_train, y_train)
estimator2.fit(x_train, y_train)
y_pre1 = estimator1.predict(x_test)
y_pre2 = estimator2.predict(x_test)
print(f'单一决策树预测结果：{y_pre1}')
print(f'AdaBoost预测结果：{y_pre2}')
# 模型评估
print(f'单一决策树准确率：{accuracy_score(y_test, y_pre1)}')
print(f'AdaBoost准确率：{accuracy_score(y_test, y_pre2)}')

