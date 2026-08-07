"""
手写数字识别
    图片由28*28 像素组成，我们的csv文件有784列，每列代表一个像素值。
    我们的目标是根据像素值预测图片中的数字。
    我们将使用KNN算法来完成这个任务。
"""
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
import joblib
from collections import Counter
from sympy.utilities.exceptions import ignore_warnings
plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文显示
plt.rcParams['axes.unicode_minus'] = False     # 正常显示负号
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# 定义函数显示索引对应图片
def show_digit(idx):
    # 读取数据集
    df = pd.read_csv('./data/digits.csv') # 100行780列
    # df.info()
    # 判断索引是否越界
    if idx < 0 or idx >= len(df):
        print('索引越界')
        return
    x = df.iloc[:, 1:]
    y = df.iloc[:, 0]
    print(f'图片的数字是：{y.iloc[idx]}')
    print(f'查看标签分布：{Counter(y)}')
    # 查看x的形状
    print(x.iloc[idx].shape)
    # print(x.iloc[idx].values)
    # print(x.iloc[idx].values.reshape(28, 28))
    x = x.iloc[idx].values.reshape(28, 28)
    # 显示图片
    plt.imshow(x, cmap='gray')
    plt.title(f'the number is:{y.iloc[idx]}')
    plt.axis('off') # 关闭坐标轴
    plt.show()

# 训练模型KNN
def train_model():
    # 读取数据集
    df = pd.read_csv('./data/digits.csv')
    x = df.iloc[:, 1:].values
    y = df.iloc[:, 0].values
    print(f'x的形状是：{x.shape}')
    print(f'y的形状是：{y.shape}')
    print(f'查看标签分布：{Counter(y)}')
    x = x / 255
    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)

    # 训练模型
    estimator = KNeighborsClassifier(n_neighbors=3)
    estimator.fit(X_train, y_train)
    # 预测
    y_pred = estimator.predict(X_test)
    print(f'预测结果是：{y_pred}')
    # 模型评估

    print(f'模型准确率是：{estimator.score(X_test, y_test)}')
    print(f'模型准确率是：{accuracy_score(y_test, y_pred)}')
    # 保存模型
    joblib.dump(estimator, './model/estimator.pkl') #保存对象 保存路径
    print("保存成功")

# 测试模型
def use_model():
    # 加载模型
    x = plt.imread('./data/demo.png')
    # 绘制图形
    plt.imshow(x, cmap='gray')
    plt.show()
    estimator = joblib.load('./model/estimator.pkl')
    # 预测
    print(x.shape) #28*28
    x = x.reshape(1, -1)
    print(x.shape)
    y_pred = estimator.predict(x)
    print(f'预测结果是：{y_pred}')

# 测试
if __name__=='__main__':
    show_digit(33)
    # train_model()
    # use_model()