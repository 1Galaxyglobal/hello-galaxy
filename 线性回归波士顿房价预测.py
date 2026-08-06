"""
    波士顿房价预测 线性回归算法 有标签 有特征 标签连续
    正规方程法
    一元线性回归 一个特征列一个标签列 y = wx + b
    多元线性回归 多个特征列一个标签列 y = w1x1 + w2x2 + ... + wnxn + b
    如何衡量模型好坏 ： 预测值与真实值之间的差异为误差 误差越小，模型越好
    最小二乘            每个样本误差平方和
    MSE均方误差         每个样本误差平方和/样本总数
    RMSE均方根误差      均方误差的平方根
    MAE平均绝对误差      绝对误差的平均值
    如何减小误差：
        梯度下降法  ——>全梯度下降（FGD） 随机梯度下降（SGD） 小批量梯度下降（MIn-Batch） 随机平均梯度下降（SAG）
        正规方程法
"""
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import Ridge,RidgeCV
from sklearn.linear_model import SGDRegressor

import numpy as np
import pandas as pd

# 数据导入
data_url = "http://lib.stat.cmu.edu/datasets/boston"
raw_df = pd.read_csv(data_url, sep="\\s+", skiprows=22, header=None)
data = np.hstack([raw_df.values[::2, :], raw_df.values[1::2, :2]])
target = raw_df.values[1::2, 2]
# print(f'特征{data.shape}')
# print(f'标签{target.shape}')
# 数据预处理
x_train, x_test,y_train,y_test = train_test_split(data,target,test_size=0.2,random_state=23)
# 特征工程
transfer = StandardScaler()
x_train = transfer.fit_transform(x_train)
x_test = transfer.transform(x_test)
# 模型训练
estimator = LinearRegression(fit_intercept=True) # 正规方程法
estimator.fit(x_train,y_train)
# 模型评估
y_predict = estimator.predict(x_test)
# print(f'权重{estimator.coef_}')
# print(f'偏置{estimator.intercept_}')
# print(f'模型预测值{y_predict}')
print(f'模型MAE平均绝对误差{mean_absolute_error(y_test,y_predict)}')
print(f'模型MSE均方误差{mean_squared_error(y_test,y_predict)}')
print(f'模型RMSE均方根误差{np.sqrt(mean_squared_error(y_test,y_predict))}')

# 随机梯度下降法
estimator = SGDRegressor(max_iter=1000, tol=1e-3, fit_intercept=True, random_state=23, loss='squared_error', eta0=0.01, learning_rate='constant')
estimator.fit(x_train,y_train)
y_pre = estimator.predict(x_test)
print(f'模型预测值{y_pre}')
print(f'模型MAE平均绝对误差{mean_absolute_error(y_test,y_pre)}')
print(f'模型MSE均方误差{mean_squared_error(y_test,y_pre)}')
print(f'模型RMSE均方根误差{np.sqrt(mean_squared_error(y_test,y_pre))}')

"""
线性回归API
    线性回归是机器学习中最简单和最常用的一种回归算法。它通过拟合一个线性模型来预测目标变量。
    线性回归模型的形式为：y = wx + b其中，w是模型的权重，b是模型的偏置。
    有监督学习，有标签，有特征，标签连续
    一元线性回归模型的形式为：y = wx + b 一个特征列+一个标签列
    多元线性回归模型的形式为：y = w1x1 + w2x2 + ... + wnxn + b 多个特征列+一个标签列
    误差 = 预测值 - 真实值
    损失函数 = 误差平方和（MSE） = (预测值 - 真实值)²
    损失函数 = 均方根误差（RMSE） = √(预测值 - 真实值)²
    损失函数 = 绝对误差平方和（MAE） = |预测值 - 真实值|
    最小二乘法：通过最小化损失函数来求解模型参数，求偏导
    让损失函数最小化:梯度下降法 正规方程法

    矩阵运算
    1范数：向量中各个元素绝对值之和
    2范数：向量中各个元素平方和的平方根
    p范数：向量中各个元素的p次方和的1/p次方
    方阵：行数等于列数的矩阵
    单位矩阵：对角线元素为1，其他元素为0的方阵
    对称矩阵：矩阵转置等于原矩阵的矩阵

"""


# 数据导入
x_train = [[166], [170], [172], [174], [176], [178], [180]] # 训练集特征
y_train = [59, 60, 61, 62, 63, 64, 65]                      # 训练集标签
x_test = [[190]]                                            # 测试集特征
# 预处理
# 特征工程
# 模型训练
estimator = LinearRegression()  # 创建线性回归模型对象
estimator.fit(x_train, y_train)
print(f'模型的权重是：{estimator.coef_}, 模型的偏置是：{estimator.intercept_}')
y_pred = estimator.predict(x_test)

# 模型预测
print(f'测试集的预测结果是：{y_pred}')