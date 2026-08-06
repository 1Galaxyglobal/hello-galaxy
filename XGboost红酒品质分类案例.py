"""
    通过 XGBoost 极限梯度提升树 底层采取打分函数 决定是否分支
    如果 Gain 值 > 0 选择分支 否则不考虑
"""
import numpy as np
import pandas as pd
from collections import Counter             # 统计数据
from sklearn.model_selection import train_test_split,StratifiedKFold    # 切分数据集，分层K折交叉验证
from sklearn.metrics import classification_report, accuracy_score
import joblib                               # 保存模型
import xgboost as xgb                       # 极限梯度提升树对象

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
    x_train = np.array(x_train)

if __name__ == "__main__":
    load_data()