"""
KNN 算法实现
先算距离，欧式距离； √（d1-d2）²+（c1-c2）²+...+（a1-a2）² 测试集与训练集的距离
然后升序排序，找到最近的K个样本，最后投票表决，得到最终结果——分类
K个样本算平均值，得到最终结果——回归
实现思路：
分类问题：有特征 有不连续标签
回归问题：有特征 有连续标签
代码实现：
导包 准备数据集（测试集合训练集） 创建模型对象 模型训练 模型预测

"""
from sklearn.neighbors import KNeighborsClassifier
x_train = [[0],[1],[2],[3]] #训练集的特征数据
y_train = [0, 0, 1, 1]      #训练集的标签数据
knn = KNeighborsClassifier(n_neighbors=3) #创建模型对象
knn.fit(x_train, y_train)#模型训练
x_test = [[1.51]]#测试集的特征数据
y_pred = knn.predict(x_test)#模型预测
# print(f'预测值为：{y_pred}')

#回归问题
from sklearn.neighbors import KNeighborsRegressor
x_train1 = [[0,0,1],[1,1,0],[3,10,14],[4,11,12]]
y_train1 = [0.3, 0.1, 0.3, 0.5]
x_test = [[3,11,10]]
model = KNeighborsRegressor(n_neighbors=2) #创建模型对象
model.fit(x_train1, y_train1)#模型训练
y_pred = model.predict(x_test)#模型预测
# print(f'预测值为：{y_pred}')


