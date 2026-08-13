"""
    基于用户的 年收入 和 消费指数 根据用户的相似性 进行聚类
    相似性：通过计算用户之间的距离来实现聚类
    聚类：将用户划分为多个簇，使得簇内用户相似，簇间用户不相似
    K-means 算法步骤：
    1. 初始化K个簇中心
    2. 计算每个样本点到簇中心的距离
    3. 根据距离将样本点分配到簇中
    4. 计算簇中心
    5. 重复步骤2-4，直到簇中心不再变化
"""
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.metrics import calinski_harabasz_score,silhouette_score
import pandas as pd
import os
os.environ['OMP_NUM_THREADS'] = '7'

def read_data():
    data = pd.read_csv('./data/customers.csv')
    # data.info()
    sse_list = []   # 定义sse列表 记录:每个K值的sse值 只考虑簇内 越小越好
    ch_list = []   # 定义Calinski-Harabasz指数列表 记录:每个K值的Calinski-Harabasz指数值
    sc_list = []   # 定义Silhouette系数列表 记录:每个K值的Silhouette系数值 只考虑簇间和簇内 越大越好
    x = data.iloc[:, 3:5]
    for k in range(2, 20):
        estimator = KMeans(n_clusters=k, max_iter=100, random_state=0)
        estimator.fit(x)
        y_pre = estimator.predict(x)
        sse_list.append(estimator.inertia_)
        ch_list.append(calinski_harabasz_score(x, y_pre))
        sc_list.append(silhouette_score(x, y_pre))
    print(sse_list)
    print(ch_list)
    print(sc_list)
    plt.figure(figsize=(20, 10), dpi=100) # 定义图形大小
    plt.plot(range(2, 20), sse_list, marker='o')
    plt.show()
    plt.plot(range(2, 20), ch_list, marker='o')
    plt.show()
    plt.plot(range(2, 20), sc_list, marker='o')
    plt.show()

def train_predict():
    data = pd.read_csv('./data/customers.csv')
    x = data.iloc[:, 3:5]
    estimator = KMeans(n_clusters=5, max_iter=100, random_state=53)
    estimator.fit(x)
    y_pre = estimator.predict(x)
    print(y_pre)
    # 绘制五个簇的散点图
    plt.scatter(x.values[y_pre == 0, 0], x.values[y_pre == 0, 1], c='red', marker='o')
    plt.scatter(x.values[y_pre == 1, 0], x.values[y_pre == 1, 1], c='blue', marker='o')
    plt.scatter(x.values[y_pre == 2, 0], x.values[y_pre == 2, 1], c='green', marker='o')
    plt.scatter(x.values[y_pre == 3, 0], x.values[y_pre == 3, 1], c='yellow', marker='o')
    plt.scatter(x.values[y_pre == 4, 0], x.values[y_pre == 4, 1], c='black', marker='o')
    plt.scatter(x.values[y_pre == 5, 0], x.values[y_pre == 5, 1], c='purple', marker='o')
    plt.show()
    # 绘制簇中心
    plt.scatter(estimator.cluster_centers_[:, 0], estimator.cluster_centers_[:, 1], c='red', marker='x')
    plt.xlabel('Income')
    plt.ylabel('Spending Score')
    plt.title('K-means Clustering')
    plt.show()

if __name__ == '__main__':
    # read_data()
    train_predict()

