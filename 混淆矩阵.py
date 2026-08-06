"""
    混淆矩阵：用来描述真实值和预测值之间的关系
    精确率 召回率
                    预测标签（正例）    预测标签（反例）
      真实标签（正例）   真正例（TP）       伪反例（FN）
      真实标签（反例）   伪正例（FP）       真反例（TN）
    精确率 = TP/（TP+FP）
    召回率 = TP/（TP+FN）
    F1 = 2 * （精确率 * 召回率）/（精确率 + 召回率）

"""
import pandas as pd
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score  # 混淆矩阵 精确率 召回率 F1值
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

data = pd.read_csv('./data/cancer.csv')
y_train = ['恶性', '良性','恶性','恶性','恶性','恶性','恶性','良性','良性','良性']
y_preA = ['恶性', '恶性','良性','良性','良性','良性','恶性','良性','良性','良性']
y_preB = ['恶性', '恶性','恶性','恶性','恶性','恶性','恶性','恶性','恶性','良性']
label = ['恶性', '良性']
df_label = ['恶性(正例)', '良性(反例)']
cm_A = confusion_matrix(y_train, y_preA, labels=label)
df_A = pd.DataFrame(cm_A, index=label, columns=df_label)
print(f'混淆矩阵A的DataFrame是 \n {df_A}')
print(f'混淆矩阵A是 \n {cm_A}')
print(f'精确率A是 {precision_score(y_train, y_preA, pos_label="恶性")}')
print(f'召回率A是 {recall_score(y_train, y_preA, pos_label="恶性")}')
print(f'F1值A是 {f1_score(y_train, y_preA, pos_label="恶性")}')

cm_B = confusion_matrix(y_train, y_preB, labels=label)
df_B = pd.DataFrame(cm_B, index=label, columns=df_label)
print(f'混淆矩阵B的DataFrame是 \n {df_B}')
print(f'混淆矩阵B是 \n {cm_B}')
print(f'精确率B是 {precision_score(y_train, y_preB,pos_label="恶性")}')
print(f'召回率B是 {recall_score(y_train, y_preB,pos_label="恶性")}')
print(f'F1值B是 {f1_score(y_train, y_preB,pos_label="恶性")}')
