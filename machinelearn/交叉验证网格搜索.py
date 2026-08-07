"""
交叉验证网格搜索
    原理：把数据分成N份
    每次取一份数据作为测试集，其余的N-1份数据作为训练集
    重复N次，每次使用不同的测试集 ——> N折交叉验证
    最终取平均值作为模型的评估结果
    例如：4折交叉验证，把数据分成4份，每份作为测试集，其余3份作为训练集，重复4次，每次使用不同的测试集，最终取平均值作为模型的评估结果
    || 次数 || 验证集（测试集）  || 训练集  ||      操作        ||  结果  ||
    ||------||----------------||--------||-----------------||--=-----||
    || 第1次 || 第1份数据 || 第2+3+4份数据 || 训练模型，模型预测 || 准确率1 ||
    || 第2次 || 第2份数据 || 第1+3+4份数据 || 训练模型，模型预测 || 准确率2 ||
    || 第3次 || 第3份数据 || 第1+2+4份数据 || 训练模型，模型预测 || 准确率3 ||
    || 第4次 || 第4份数据 || 第1+2+3份数据 || 训练模型，模型预测 || 准确率4 ||
    最终准确率 = (准确率1 + 准确率2 + 准确率3 + 准确率4) ÷ 4
    假设 第4次最好（准确率最高），则：用第四组全部数据（训练集 + 测试集）重新训练模型，再次用此时的模型作为最终模型。
网格搜索
    原理：遍历所有可能的参数组合，选择最佳参数组合 ——> 网格搜索
    接受超参可能出现的值 然后对每个超参都进行交叉验证，选择最佳参数组合
    超参数：需要你手动录入的数据，不同的超参组合，模型的性能可能会有所不同。

"""
from sklearn.datasets import load_iris              #   加载鸢尾花测试集
from sklearn.model_selection import GridSearchCV    #   网格搜索
from sklearn.model_selection import train_test_split    #   数据集划分
from sklearn.neighbors import KNeighborsClassifier    #   K近邻分类器
from sklearn.preprocessing import StandardScaler    #   数据标准化
from sklearn.metrics import accuracy_score          #   准确率

iris_data = load_iris()
x_train, x_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=22)

transfer = StandardScaler() # 数据标准化
x_train = transfer.fit_transform(x_train)
x_test = transfer.transform(x_test)
estimator = KNeighborsClassifier(n_neighbors=5)
param_dict = {"n_neighbors": [i for i in range(1,11)]}  # 超参可能值
# 创建GridSearchCV对象 进行网格搜索+交叉验证
estimator = GridSearchCV(estimator, param_dict, cv=3)  # 网格搜索
estimator.fit(x_train, y_train)

# estimator要计算最优超参的模型  param_dict是超参可能值  cv=4 表示4折交叉验证
# 返回estimator 为处理后的最优参数模型
# print(f'最优评分{estimator.best_score_}')
# print(f'最优参数{estimator.best_params_}')
# print(f'最优估计器{estimator.best_estimator_}')
# print(f'最佳结果{estimator.cv_results_}')
#模型评估
estimator = KNeighborsClassifier(n_neighbors=3)
estimator.fit(x_train, y_train)
y_predict = estimator.predict(x_test)
# print(f'预测结果{y_predict}')
# print(f'准确率{accuracy_score(y_test, y_predict)}')
