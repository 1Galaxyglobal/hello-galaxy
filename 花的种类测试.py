from sklearn.datasets import load_iris
#作用：导入 scikit-learn 自带的鸢尾花数据集。这是一个经典的多分类数据集，包含 150 个样本，4 个特征（花萼长度、花萼宽度、花瓣长度、花瓣宽度），3 个类别。
import seaborn as sns
#作用：导入高级数据可视化库 Seaborn，通常用于绘制热力图、分布图、配对图等，让数据看起来更美观。
import pandas as pd
#作用：导入数据处理库 Pandas，用于将数据集转换为 DataFrame 格式，方便进行表格化操作和查看。
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
#作用：导入基础绘图库 Matplotlib，用于绘制折线图、散点图、柱状图等。
from sklearn.model_selection import train_test_split
#作用：导入数据集划分工具，用于将原始数据随机拆分为训练集和测试集（例如 80% 训练，20% 测试）。
from sklearn.preprocessing import StandardScaler
#作用：导入数据标准化工具。KNN 算法是基于距离的，不同特征的量纲（单位）不同会影响结果，StandardScaler 会将数据转换为均值为 0、方差为 1 的标准正态分布。
from sklearn.neighbors import KNeighborsClassifier
#作用：这就是我们刚才用过的 K近邻分类器。

#1.定义函数，加载测试集 查看数据集
def load_data():
    iris_data = load_iris()
    #查看数据集
    # print(f'数据集是：{iris_data}')
    # print(f'数据集的类型是：{type(iris)}')
    print(f'数据集的键是：{iris_data.keys()}')
    # print(f'数据集的前 5 行数据是：{iris_data.data[:5]}')
    # print(f'数据集的标签是：{iris_data.target[:5]}')
    # print(f'数据集的标签名称是：{iris_data.target_names}')
    # print(f'数据集的特征是：{iris_data.feature_names}')

#2.数据的可视化
def show_iris():
    # 加载数据集
    iris_data = load_iris()
    # 把数据集可视化 封装成DataFrame对象
    iris_df = pd.DataFrame(iris_data.data, columns=iris_data.feature_names)
    iris_df['label'] = iris_data.target
    print(iris_df)
    # 绘制散点图
    sns.lmplot(x='sepal length (cm)', y='sepal width (cm)', data=iris_df, hue='label', fit_reg= True)
    # 加hue是按照标签进行着色 加fit_reg=True是绘制回归线
    plt.title("iris data") #标题
    plt.tight_layout() #自动调整子图参数，使之填充整个图像区域 使得标题显示完整
    # 绘制对角线的直方图
    sns.pairplot(iris_df, hue='label')
    plt.show()

# 3.切分训练集和测试集
def split_train_test():
    iris_data = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=42)
    print(f'训练集特征是：{X_train}， 个数是：{X_train.shape}')
    print(f'训练集标签是：{y_train}， 个数是：{y_train.shape}')
    print(f'测试集特征是：{X_test}， 个数是：{X_test.shape}')
    print(f'测试集标签是：{y_test}， 个数是：{y_test.shape}')

# 4.模型的评估
def evaluate_model():
    iris_data = load_iris() # 加载数据集
    X_train, X_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=42)
    print(f'数据集的最大值是：{iris_data.data.max()}') # 查看数据集的最大值
    print(f'数据集的最小值是：{iris_data.data.min()}') # 查看数据集的最小值
    transfer = StandardScaler()
    X_train = transfer.fit_transform(X_train) # 数据标准化 训练 转化 适用于第一次训练
    X_test = transfer.transform(X_test)
    knn = KNeighborsClassifier(n_neighbors=3) #创建模型对象
    knn.fit(X_train, y_train) #模型训练

    y_pred = knn.predict(X_test)
    print(f'预测结果是：{y_pred}')
    print(f'实际结果是：{y_test}')

    new_data = [4.9, 2.5, 7.3, 0.2]
    new_data_transfer = transfer.transform([new_data]) # 新数据标准化

    print(f'新数据预测结果是：{knn.predict(new_data_transfer)}')
    new_data_proba = knn.predict_proba(new_data_transfer)
    print(f'新数据预测概率是：{new_data_proba}')

# 5.模型的准确率
def evaluate_model_score():
    iris_data = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=42)
    transfer = StandardScaler()
    X_train = transfer.fit_transform(X_train)  # 数据标准化 训练 转化 适用于第一次训练
    X_test = transfer.transform(X_test)
    knn = KNeighborsClassifier(n_neighbors=3)  # 创建模型对象
    knn.fit(X_train, y_train)  # 模型训练
    y_pred = knn.predict(X_test)
    new_data = [4.9, 2.5, 7.3, 0.2]
    new_data_transfer = transfer.transform([new_data]) # 新数据标准化
    print(f'新数据预测结果是：{knn.predict(new_data_transfer)}')
    new_data_proba = knn.predict_proba(new_data_transfer)
    print(f'新数据预测概率是：{new_data_proba}')
    print(f'准确率是：{knn.score(X_test, y_test)}')
    print(f'准确率是：{accuracy_score(y_test, y_pred)}')


if __name__ == '__main__':
    load_data()
    show_iris()
    split_train_test()
    evaluate_model()
    evaluate_model_score()
