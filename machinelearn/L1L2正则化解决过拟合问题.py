"""
    欠拟合 正好拟合 过拟合 L1 L2 正则化 效果图
    欠拟合：模型在测试集和训练集表现都不好 模型太简单——>增加特征 增加模型复杂度
    正好拟合：模型在测试集和训练集表现都很好
    过拟合: 模型在训练集表现好 但是在测试集表现不好 模型太复杂——>减小特征 手动筛选特征——>L1L2 正则化
    L1 L2 正则化：通过在损失函数中添加正则化项来防止过拟合
    L1正则化：对模型参数的绝对值求和
    L2正则化：对模型参数的平方求和
    L1正则化可以用于特征选择，因为如果某个特征的系数被L1正则化项设置为0，则该特征将被完全忽略
    L2正则化可以用于防止过拟合，因为如果某个特征的系数被L2正则化项设置为0，则该特征的系数将被缩小，从而使模型更简单 推荐L2
    L1/L2 思路都是通过增加惩罚系数来修正权重 惩罚系数越大 修改力度越大
    L1可以使权重为0 从而达到选择特征的目的 L2只能让权重缩小接近0 不能为0

"""
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge, RidgeCV, Lasso
from sklearn.metrics import mean_squared_error,root_mean_squared_error,root_mean_squared_log_error
import matplotlib.pyplot as plt
import numpy as np

# 定义欠拟合函数
def underfitting():
    # 导入数据
    np.random.seed(23) # 设置随机种子使得每次生成的数据固定
    x = np.random.uniform(-3, 3, 100) # 生成100个-3到3的随机数
    y = 0.5 * x ** 2 + x + 2 + np.random.normal(0, 1, 100) # 线性公式 参数1：平均值 参数2：标准差 参数3：个数
    # x 为特征，y 为标签
    # print(f'x.shape:{x.shape}, y.shape:{y.shape}') # 打印数据形状
    x = x.reshape(-1, 1)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=23)
    estimator = LinearRegression()
    estimator.fit(x_train, y_train)
    y_pred = estimator.predict(x_test)
    print('欠拟合模型得分:', estimator.score(x_test, y_test))
    print('欠拟合模型MSE:', mean_squared_error(y_test, y_pred))
    print('欠拟合模型RMSE:', root_mean_squared_error(y_test, y_pred))
    print('欠拟合模型RMSLE:', root_mean_squared_log_error(y_test, y_pred))
    print('欠拟合模型得分:', estimator.score(x_test, y_test))
    plt.scatter(x_test, y_test, color='black')
    plt.plot(x_test, y_pred, color='red')
    plt.show()

# 定义正好拟合函数
def just_right():
    np.random.seed(43) # 设置随机种子使得每次生成的数据固定
    x = np.random.uniform(-3, 3, 100) # 生成100个-3到3的随机数
    y = 0.5 * x ** 5 + 100 * x ** 3 + 2 + np.random.normal(0, 1, 100) # 线性公式 参数1：平均值 参数2：标准差 参数3：个数
    X = x.reshape(-1, 1)
    x2 = np.hstack([X, X ** 2, X ** 3, X ** 4, X ** 5])  # 加上 x³, x⁴, x⁵ 的 polynomial 特征
    estimator = LinearRegression()
    estimator.fit(x2, y)
    y_pred = estimator.predict(x2)
    print('正好拟合模型得分:', estimator.score(x2, y))
    print('正好拟合模型MSE:', mean_squared_error(y, y_pred))
    print('正好拟合模型RMSE:', root_mean_squared_error(y, y_pred))
    print('正好拟合模型得分:', estimator.score(x2, y))
    plt.scatter(x, y)
    # np.sort(x) # 对x轴排序 升序
    plt.plot(np.sort(x), y_pred[np.argsort(x)], color='red')
    plt.show()

# 定义过拟合函数
def overfitting():
    np.random.seed(23) # 设置随机种子使得每次生成的数据固定
    x = np.random.uniform(-3, 3, 100) # 生成100个-3到3的随机数
    y = 0.5 * x ** 2 + x + 2 + np.random.normal(0, 1, 100)# 线性公式 参数1：平均值 参数2：标准差 参数3：个数
    X = x.reshape(-1, 1)
    x3 = np.hstack([X, X ** 2, X ** 3, X ** 4, X ** 5, X ** 6, X ** 7, X ** 8])
    estimator = LinearRegression()
    estimator.fit(x3, y)
    y_pred = estimator.predict(x3)
    print('过拟合模型得分:', estimator.score(x3, y))
    print('过拟合模型MSE:', mean_squared_error(y, y_pred))
    print('过拟合模型RMSE:', root_mean_squared_error(y, y_pred))
    print('过拟合模型得分:', estimator.score(x3, y))
    plt.scatter(x, y, color='black')
    plt.plot(np.sort(x), y_pred[np.argsort(x)], color='red')
    plt.show()

# L1正则化
def L1_regularization():
    np.random.seed(23)
    x = np.random.uniform(-3, 3, 100)
    y = 0.5 * x ** 2 + x + 2 + np.random.normal(0, 1, 100) # 线性公式 参数1：平均值 参数2：标准差 参数3：个数
    X = x.reshape(-1, 1)
    x3 = np.hstack([X, X ** 2, X ** 3, X ** 4, X ** 5, X ** 6, X ** 7, X ** 8])
    estimator = Lasso(alpha=0.1)
    estimator.fit(x3, y)
    y_pred = estimator.predict(x3)
    print('过拟合模型得分:', estimator.score(x3, y))
    print('过拟合模型MSE:', mean_squared_error(y, y_pred))
    print('过拟合模型RMSE:', root_mean_squared_error(y, y_pred))
    print('过拟合模型得分:', estimator.score(x3, y))
    plt.scatter(x, y, color='black')
    plt.plot(np.sort(x), y_pred[np.argsort(x)], color='red')
    plt.show()

def L2_regularization():
    np.random.seed(23)
    x = np.random.uniform(-3, 3, 100)
    y = 0.5 * x ** 2 + x + 2 + np.random.normal(0, 1, 100)
    X = x.reshape(-1, 1)
    x3 = np.hstack([X, X ** 2, X ** 3, X ** 4, X ** 5, X ** 6, X ** 7, X ** 8, X ** 9])
    estimator = Ridge(alpha=15)
    estimator.fit(x3, y)
    y_pred = estimator.predict(x3)
    print('过拟合模型得分:', estimator.score(x3, y))
    print('过拟合模型MSE:', mean_squared_error(y, y_pred))
    print('过拟合模型RMSE:', root_mean_squared_error(y, y_pred))
    print('过拟合模型得分:', estimator.score(x3, y))
    plt.scatter(x, y, color='black')
    plt.plot(np.sort(x), y_pred[np.argsort(x)], color='red')
    plt.show()

if __name__ == '__main__':
    # underfitting()
    # just_right()
    # overfitting()
    # L1_regularization()
    L2_regularization()