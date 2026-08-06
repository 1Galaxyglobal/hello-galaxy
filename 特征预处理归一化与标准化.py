"""
特征预处理归一化:
特征提取
特征预处理（归一化，标准化）
特征降维
特征选择
特征组合

特征预处理标准化:


归一化：防止量纲问题导致误差较大
x' = (x - x_min) / (x_max - x_min)
x'' = x' * (max - min) + min ——>最终结果
弊端：容易受异常值影响——>用于处理小数据集

"""

#导包归一化
from sklearn.preprocessing import MinMaxScaler
x_train = [[90, 2, 40], [80, 60, 40], [70, 80, 45]]
mms = MinMaxScaler()
x_train_new = mms.fit_transform(x_train)
print("归一化处理后的数据")
print(x_train_new)

"""
标准化：将数据转换为均值为0，方差为1的正态分布
x' = (x - x_mean) / x_std
适用于大数据集处理
"""

from sklearn.preprocessing import StandardScaler
x_train1 = [[90, 21, 40, 99], [12, 80, 60, 40], [22, 70, 80, 45]]
transfer = StandardScaler()
x_train_new1 = transfer.fit_transform(x_train1)
print(x_train_new1)
print(f'数据集的均值为：{transfer.mean_}')
print(f'数据集的方差为：{transfer.var_}')

