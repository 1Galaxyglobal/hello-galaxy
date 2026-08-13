"""
    K-means 聚类算法 : 无监督学习，有特征，有标签，根据样本间的相似度进行划分
    相似度：通过计算样本点与簇中心的距离来实现聚类
    簇中心：样本点的集合，用于表示簇的特征
    距离度量：用于计算样本点与簇中心之间的距离
    聚类：将样本点划分为多个簇，使得簇内样本点相似，簇间样本点不相似
    K-means 算法步骤：
        1. 初始化：随机选择 K 个样本点作为初始簇中心
        2. 分配：将每个样本点分配给最近的簇中心，形成 K 个簇
        3. 更新：计算每个簇的簇中心，即簇内所有样本点的平均值
        4. 重复步骤 2 和 3，直到簇中心不再变化或达到最大迭代次数
"""
from sklearn.cluster import KMeans
import os
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.datasets import make_blobs             # 生成数据集(按照正态分布生成)
from sklearn.metrics import calinski_harabasz_score # 轮廓系数
os.environ['OMP_NUM_THREADS'] = '4'                 # 设置线程多数，加速计算

# 生成数据集
x, y = make_blobs(n_samples=300, centers=[[-1,1], [1,1], [1,2], [-2,-1]], cluster_std=[0.60, 0.80, 1.00, 1.20], random_state=55)
# n_samples: 样本点数量 centers: 簇中心数量 cluster_std: 簇内样本点标准差 random_state: 随机种子
# print(x.shape, y.shape)
plt.scatter(x[:,0], x[:,1], c=y)
plt.show()

estimator = KMeans(n_clusters=4, random_state=55)
estimator.fit(x)
y_pred = estimator.predict(x)

plt.scatter(x[:,0], x[:,1], c=y_pred)
plt.scatter(estimator.cluster_centers_[:,0], estimator.cluster_centers_[:,1], c='red', marker='x')
plt.show()

print(f'预测结果是：{y_pred}')
print(f'簇中心是：{estimator.cluster_centers_}')
print(f'簇内样本点数量是：{estimator.labels_.shape}')
print(f'轮廓系数是：{silhouette_score(x, y_pred)}')
print(f'评分是：{calinski_harabasz_score(x, y_pred)}') # 轮廓系数

