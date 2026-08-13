"""
    K-means 聚类算法评估指标:
    SSE(误差平方和)、Calinski-Harabasz指数、Silhouette系数
    SSE(误差平方和)：衡量数据点与簇中心之间距离的平方和，越小越好 随K值增大 SSE值减小 趋于平缓 目标是找到一个K值，使得SSE值开始显著下降或趋于平缓
    Calinski-Harabasz指数：衡量簇内距离与簇间距离的比值，越大越好 随K值增大 Calinski-Harabasz指数值增大 趋于平缓 目标是找到一个K值，使得Calinski-Harabasz指数值开始显著下降或趋于平缓
    Silhouette系数：衡量样本点与簇内其他样本点的距离与簇间其他样本点的距离的比值，越大越好 随K值增大 Silhouette系数值增大 趋于平缓 目标是找到一个K值，使得Silhouette系数值开始显著下降或趋于平缓
    思路1: SSE + 肘部法
    思路2: Calinski-Harabasz指数 + 肘部法
    思路3: Silhouette系数 + 肘部法
    肘部法：通过观察 SSE、Calinski-Harabasz指数、Silhouette系数随簇数量变化的趋势，选择一个合适的簇数量，使得指标值开始显著下降或趋于平缓 目标是找到一个K值，使得指标值开始显著下降或趋于平缓
"""

from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from sklearn.metrics import calinski_harabasz_score
from sklearn.metrics import silhouette_score
import os
os.environ['OMP_NUM_THREADS'] = '30'
def dm01_sse():
    sse_list = [] # 定义sse列表 记录:每个K值的sse值
    # 生成数据集 参1:样本点数量 参2:特征数量 参3:簇中心数量 参4:簇内样本点标准差 参5:随机种子
    x, y = make_blobs(n_samples=1000, n_features=2, centers=[[-1, -1], [0, 0], [1, 1], [2, 2]],
                      cluster_std=[0.4, 0.2, 0.2, 0.2], random_state=22)
    for k in range(1, 100):
        estimator = KMeans(n_clusters=k, max_iter=100, random_state=0) # 参1:簇数量 参2:最大迭代次数 参3:随机种子
        estimator.fit(x)
        sse_list.append(estimator.inertia_) # 获取sse的值
    print(sse_list)
    plt.figure(figsize=(20, 10), dpi=100) # 定义图形大小
    plt.title('SSE')
    plt.xticks(range(0, 100, 3), labels=range(0, 100, 3)) # 定义x轴刻度
    plt.grid() # 添加网格
    plt.plot(range(1, 100), sse_list, 'or-') # 参1:横坐标 参2:纵坐标 参3:标记样式
    plt.show()

def dm02_ch():
    ch_index_list = [] # 定义Calinski-Harabasz指数列表 记录:每个K值的Calinski-Harabasz指数值
    x, y = make_blobs(n_samples=1000, n_features=2, centers=[[-1, -1], [0, 0], [1, 1], [2, 2]],
                      cluster_std=[0.4, 0.2, 0.2, 0.2], random_state=22)
    for k in range(4, 100):
        estimator = KMeans(n_clusters=k, max_iter=100, random_state=0) # 参1:簇数量 参2:最大迭代次数 参3:随机种子
        estimator.fit(x)
        ch_index_list.append(calinski_harabasz_score(x, estimator.labels_)) # 获取Calinski-Harabasz指数的值
    print(ch_index_list)
    plt.figure(figsize=(20, 10), dpi=100) # 定义图形大小
    plt.title('Calinski-Harabasz Index')
    plt.xticks(range(0, 100, 3), labels=range(0, 100, 3)) # 定义x轴刻度
    plt.grid() # 添加网格
    plt.plot(range(4, 100), ch_index_list, 'or-') # 参1:横坐标 参2:纵坐标 参3:标记样式
    plt.show()

def dm03_sc():
    sil_coeff_list = [] # 定义Silhouette系数列表 记录:每个K值的Silhouette系数值
    x, y = make_blobs(n_samples=1000, n_features=2, centers=[[-1, -1], [0, 0], [1, 1], [2, 2]],
                      cluster_std=[0.4, 0.2, 0.2, 0.2], random_state=22)
    for k in range(5, 100):
        estimator = KMeans(n_clusters=k, max_iter=100, random_state=81) # 参1:簇数量 参2:最大迭代次数 参3:随机种子
        estimator.fit(x)
        y_pre = estimator.predict(x)
        sc_value = silhouette_score(x, y_pre)
        sil_coeff_list.append(sc_value) # 获取Silhouette系数的值
    print(sil_coeff_list)
    plt.figure(figsize=(20, 10), dpi=100) # 定义图形大小
    plt.title('Silhouette Coefficient')
    plt.xticks(range(0, 100, 3)) # 定义x轴刻度
    plt.grid() # 添加网格
    plt.xlabel('K') # 添加x轴标签
    plt.ylabel('Silhouette Coefficient')
    plt.plot(range(5, 100), sil_coeff_list, 'or-') # 参1:横坐标（与k的范围保持一致） 参2:纵坐标 参3:标记样式
    plt.show()

if __name__ == '__main__':
    # dm01_sse()
    dm02_ch()
    # dm03_sc()
