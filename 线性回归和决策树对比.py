"""
    线性回归：有标签 有特征 标签连续
    CART回归决策树： 既可以做分类，也可以做回归，一般用来做分类
    做分类：基尼值 做回归：平方损失
"""
from sklearn.tree import DecisionTreeRegressor # 回归决策树
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression # 线性回归

from machinelearn.交叉验证网格搜索 import estimator, x_test

x_train = np.array(list(range(1, 11))).reshape(-1, 1)
y_train = np.array([1.0, 1.7, 2.5, 3.9, 4.5, 5.5, 6.3, 7.0, 8.0, 9.0])
# print(x_train)
# print(y_train)
estimator1 = LinearRegression()
estimator2 = DecisionTreeRegressor(max_depth=1)
estimator3 = DecisionTreeRegressor(max_depth=3)
estimator1.fit(x_train, y_train)
estimator2.fit(x_train, y_train)
estimator3.fit(x_train, y_train)

x_test = np.arange(1, 11, 0.1).reshape(-1, 1)
y_predict1 = estimator1.predict(x_test)
y_predict2 = estimator2.predict(x_test)
y_predict3 = estimator3.predict(x_test)
print(f'线性回归预测值 \n {y_predict1}')
print(f'CART回归预测值深度为1 \n {y_predict2}')
print(f'CART回归预测值深度为3 \n {y_predict3}')
plt.scatter(x_train, y_train, c = 'gray')
plt.plot(x_test, y_predict1, c = 'red', label = 'LinearRegression')
plt.plot(x_test, y_predict2, c = 'green', label = 'DecisionTreeRegressor(max_depth=1)')
plt.plot(x_test, y_predict3, c = 'blue', label = 'DecisionTreeRegressor(max_depth=3)')
plt.legend()
plt.xlabel('data')
plt.ylabel('target')
plt.title('DecisionTreeRegressor')
plt.show()