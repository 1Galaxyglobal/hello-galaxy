"""
    通过逻辑回归算法搭建模型
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score,roc_auc_score,recall_score,precision_score,f1_score,classification_report
# 准确率 精确率 召回率 F1值 分类评估报告

# 数据加载
def load_data():
    data = pd.read_csv('./data/churn.csv')
    data.dropna(axis=0, inplace=True)  # 删除有缺失值的行
    # data.info()
    # 因为 churn 和 Gender是字符串 所以需要转换为数值
    churn_df = pd.get_dummies(data, columns=['Churn', 'Gender'])
    # print(churn_df.head(5))
    # 修改列名
    churn_df.rename(columns={'Churn_Yes': 'Flag'}, inplace=True)
    print(churn_df.head(5))
    print(churn_df.Flag.value_counts()) # 查看标签列的分布 有多少个True 有多少个False

# 数据可视化
def data_visualize():
    data = pd.read_csv('./data/churn.csv')
    churn_df = pd.get_dummies(data, columns=['Churn', 'Gender'])
    churn_df.rename(columns={'Churn_Yes': 'Flag'}, inplace=True)
    # print(churn_df.columns)
    """列名如下
    ['CustomerID', 'PartnerATT', 'DependentsATT', 'Landline',
       'InternetService', 'PaymentMethod', 'Contract', 'StreamingTV',
       'StreamingMovies', 'MonthlyCharges', 'TotalCharges', 'TenureMonths',
       'Churn_No', 'Flag', 'Gender_Female', 'Gender_Male']
    """
    # 绘图
    sns.countplot(x='InternetService', data=churn_df, hue='Flag')
    plt.ylim(0, 500) # 设置y轴的显示范围
    plt.show()

# 逻辑回归
def feature_engineering():
    data = pd.read_csv('./data/churn.csv')
    data.rename(columns={'Churn_Yes': 'Flag'}, inplace=True)

    churn_df = pd.get_dummies(data, columns=['Churn', 'Gender'])
    # print(churn_df.columns)
    """,MonthlyCharges,TotalCharges,TenureMonths 数
    ['CustomerID', 'PartnerATT', 'DependentsATT', 'Landline',
       'InternetService', 'PaymentMethod', 'Contract', 'StreamingTV',
       'StreamingMovies', 'MonthlyCharges', 'TotalCharges', 'TenureMonths',
       'Churn_No', 'Churn_Yes', 'Gender_Female', 'Gender_Male'],
    """
    x = churn_df[['MonthlyCharges', 'TenureMonths','TotalCharges']]
    churn_df.rename(columns={'Churn_Yes': 'Flag'}, inplace=True)
    churn_df.drop(['Gender_Female', 'Churn_No'], axis=1, inplace=True)  # 删除无用的列
    y = churn_df['Flag']
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    estiamtor = LogisticRegression()
    estiamtor.fit(x_train, y_train)
    y_pre = estiamtor.predict(x_test)
    print(y_pre)
    print(f'预测前准确率：{estiamtor.score(x_test, y_test)}')
    print(f'预测后准确率：{accuracy_score(y_test, y_pre)}')
    print(f'混淆矩阵：\n {confusion_matrix(y_test, y_pre)}')
    print(f'精确率：{precision_score(y_test, y_pre)}')
    print(f'召回率：{recall_score(y_test, y_pre)}')
    print(f'F1值：{f1_score(y_test, y_pre)}')
    print(f'分类评估报告：\n {classification_report(y_test, y_pre)}')
    print(f'AUC值：{roc_auc_score(y_test, y_pre)}')

if __name__ == '__main__':
    # load_data()
    data_visualize()
    # feature_engineering()