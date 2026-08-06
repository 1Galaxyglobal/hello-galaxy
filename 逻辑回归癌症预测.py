"""
逻辑回归：有特征 有标签 标签离散 适合二分类
原理：
    把线性回归处理后的预测值通过Sigmoid激活函数 映射到[0,1]概率 基于自定义的阈值分类
损失函数;
    极大似然估计的负数形式
方式
    数据加载
    数据预处理
    特征工程
    模型训练
    模型预测
    模型评估
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

from machinelearn.交叉验证网格搜索 import estimator

# 数据加载
data = pd.read_csv('./data/cancer.csv')
# data.info()
data.dropna(axis=0,inplace=True) # 删除有缺失值的行
# data.info()
x = data.iloc[:, 1:-1] # 按行号 列索引获取数据 ：表示所有行， 1：-1表示从第一列到倒数第一列
# y = data.iloc[:, -1] #最后标签列
y = data.diagnosis_label # 获取标签列
# print(f'x.shape是{x.shape},y.shape是{y.shape}');
# print(x[:5])
# print(y[:5])
# 数据预处理
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
transfer = StandardScaler()
x_train = transfer.fit_transform(x_train)
x_test = transfer.transform(x_test)
# 模型训练
estimator = LogisticRegression()
estimator.fit(x_train, y_train)
# 模型预测
y_pred = estimator.predict(x_test)
print(f'预测结果是：{y_pred}')
# 模型评估
print(f'预测前评估模型准确率：{estimator.score(x_test, y_test)}') #测试集准确率
print(f'预测后评估模型准确率是：{accuracy_score(y_test, y_pred)}') #测试集准确率
