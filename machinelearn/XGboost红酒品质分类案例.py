"""
    通过 XGBoost 极限梯度提升树 底层采取打分函数 决定是否分支
    如果 Gain 值 > 0 选择分支 否则不考虑
"""
import numpy as np
import pandas as pd
from collections import Counter             # 统计数据
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV  # 切分数据集，分层K折交叉验证
from sklearn.metrics import classification_report, accuracy_score
import joblib                               # 保存模型
import xgboost as xgb                       # 极限梯度提升树对象
from sklearn.utils import class_weight


# 数据导入
def load_data():
    data = pd.read_csv("./data/红酒品质分类.csv")
    # data.info()
    x = data.iloc[:, :-1]
    y = data.iloc[:, -1] - 3 # 最后一列是标签 [0,5]
    # print(x[:5])
    # print(y[:5])
    # print(f'查看标签结果的分布情况{Counter(y)}') 发现数据范围是[3,8] 所以减3
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=23,stratify=y)
    # 把上述训练集数据和测试集数据拼接到一起 测试集数据和标签拼接到一起
    pd.concat([x_train, y_train], axis=1).to_csv("./data/红酒品质分类_train.csv", index=False)
    pd.concat([x_test, y_test], axis=1).to_csv("./data/红酒品质分类_test.csv", index=False)

# 模型训练
def train_xgb():
    train = pd.read_csv("./data/红酒品质分类_train.csv")
    test = pd.read_csv("./data/红酒品质分类_test.csv")
    x_train = train.iloc[:, :-1]
    y_train = train.iloc[:, -1]
    x_test = test.iloc[:, :-1]
    y_test = test.iloc[:, -1]
    estimator = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, objective="multi:softmax",num_class=6,random_state=55)
    # multi:softmax 多分类模型 num_class是类别数
    estimator.fit(x_train, y_train)
    y_predict = estimator.predict(x_test)
    print(f'预测结果：{y_predict}')
    print(f'准确率：{accuracy_score(y_test, y_predict)}')
    print(classification_report(y_test, y_predict))
    joblib.dump(estimator, "./model/红酒品质分类.pkl")
    print(f'保存模型成功')

# 模型预测
def predict_xgb():
    estimator = joblib.load("./model/红酒品质分类.pkl")
    train = pd.read_csv("./data/红酒品质分类_train.csv")
    test = pd.read_csv("./data/红酒品质分类_test.csv")
    x_train = train.iloc[:, :-1]
    y_train = train.iloc[:, -1]
    x_test = test.iloc[:, :-1]
    y_test = test.iloc[:, -1]
    # 创建网格搜索和交叉验证对象 找模型最优参
    param_grid = {'n_estimators': [20, 30, 40, 50],
                  'max_depth':[2, 3, 4, 9],
                  'learning_rate':[0.1,0.2,0.4,0.5]}
    # 创建分层采样对象
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=23)
    # 创建网格搜索对象
    grid_estimator = GridSearchCV(estimator, param_grid, cv=skf)
    grid_estimator.fit(x_train, y_train)
    y_predict = grid_estimator.predict(x_test)
    print(f'预测结果：{y_predict}')
    print(f'最优参数：{grid_estimator.best_estimator_}')
    print(f'最优评分：{grid_estimator.best_score_}')


if __name__ == "__main__":
    # load_data()
    # train_xgb()
    predict_xgb()