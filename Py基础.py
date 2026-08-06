# 注释
# 字体大小 调大：shift+alt+.  调小：shift+alt+,
# num = 100.1
# print(type(num))
# print(isinstance(num,int))
# st = 'ahb'
# str = """
# nihaoshijie
# zaijian
# """
# print(type(str))
# print(st + st)
# k = input()
# print(f"nihaosiji{k}udh")
# print("ycbww%scd"%k)
# num = int(input())
# num **= num
# print(num)

# + - * / //整除   %取模   **次幂  逻辑and or not !
# a = int(input())
# b = int(input())
# if(a + b > num) and (a + num > b) and (b + num > a):
#     print("yes")
# elif (a + b < num) or (a + num < b) or (b + num < a):
#     print("no")
# else:
#     print("maybe")
# match a:
#     case 1:
#         print("1")
#     case 2:
#         print("2")

# i = 0
# while i < 4:
#     print(i)
#     i += 1
# for i in range(4, 8):
#     print(i)  # 4~7 左闭右开 print每一个都换行
# for i in range(4, 11, 3):
#     print(i,end=' ')  # 4~11 左闭右开 数字间距3 print每一个不换行 数与数之间空格相连
# str = "asdfghjkl"
# for i in str:
#     if i > 'a' and i < 'g' :
#         print(i)
# for i in range(1,10):
#     for j in range(1,i+1):
#         print(f"{i} * {j} = {i * j}",end="\t")
#     print("")
# ans = 0;
# while 1:
#     a = int(input())
#     if a == 0:
#         break
#     else:
#         ans += 1
# print(f"finnal answer:{ans}")

# import random
# a = random.randint(1,100)

# list
# s = [1,2,3,"hello",True]#s[0]=1
# print(type(s))
# del s[4]#删除指定位置元素 s.remove(element)删除元素
# print(s) #s.count(element)统计元素个数 s.clear()#清空list
# for itm in s:
#     print(itm)#遍历
# print(s[2:4:1])#左闭右开 s[begin:end:step]切片
# num = [1,56,89,2,332,88,54,77,2]
# print(sorted(num))#返回一个新的升序排序列表
# print(sorted(num,reverse=True))#返回一个新的降序排序列表
# num.reverse()#列表翻转
# num.remove(2)#移除第一次出现特定元素的值
# num.insert(1,829)#在0~1之间插入元素
# num.append(999)#将元素添加到列表
# num.pop(3)#.pop(不含参)删除列表末尾的元素 pop(参数x)删除下标x的元素
# print(num)
# num = []#定义一个空列表
# ans = 0
# n = int(input())
# for i in range(0,n):
#     m = int(input())
#     ans += m
#     num.append(m)#放在容器中
# print(min(num))
# print(max(num))
# num.sort()
# print(num[0]+ans)
# print(len(num))#len()返回数组中元素个数
# num1 = [56,84,956,42,3,56,69,4]
# num2 = [69,98,4,66,56,956,4]
# num = []#去重
# for item in num1 and num2:
#     if item not in num3:#是否存在与列表之中 if num in nums:返回类型为bool
#         num3.append(item)
#     else:
#         continue
# num3 = [*num1,*num2] #快速合并两个数组
# print(sorted(num3))
# for i in range(1,21):
#     num.append(i**2)
# print(num)
# list_c = []
# rows = int(input())
# wid = int(input())
# for i in range(rows):
#     list_l = []
#     for j in range(wid):
#         val = int(input())
#         list_l.append(val)
#     list_c.append(list_l)
# for i in list_c :
#     print(sum(i))#自带sum函数 把每一行进行求和操作
# for i in list_c:
#     for j in i:
#         print(j,end=" ")
#     print()  #遍历


# 下取整
# 方法 1：使用 int()
# import math
# result = float(input())
# print(int(result))  # 3
# # 方法 2：使用 math.floor()
# print(math.floor(result))  # 3
# # 方法 3：使用 // 1
# print(result // 1)

#上取整
# import math
# result = float(input())
# print(math.ceil(result))

# 函数
# def add(a,b):
#     return a+b
#
# def lens(s):
#     length = 0
#     for i in s:
#         length += 1
#     return length  #本身自带len函数
# import math
# def prime(n):#判断质数的函数
#     if n == 1:
#         return False
#     if n == 2:
#         return True
#     res = math.sqrt(n)
#     for i in range(2,int(res)+1):
#         if n % i == 0:
#             return False
#     return True
# num3 = [i**2 for i in range(1,21) if(prime(i))] #num3中的元素为循环后i**2的值
# print(num3)#判断条件为是质数才输出

# 字符串以下所有方法不会对字符串进行任何修改
# str = "hello worLd hydRide"
# print(str[2:9:2])#字符串切片同理
# print(str.find("dri"))#第一次出现的位置 如果没有返回-1
# print(str.count("d"))#统计出现次数
# print(str.replace("d","h"))#替换old->new
# print(str.split(" "))#将字符串以空格为分隔符分割为列表['hello', 'worLd', 'hydRide']
# print(str.strip("e"))#去除字符串两端空格或指定字符
# print(str.title())#所有单词首字母大写，其余字小写
# print(str.capitalize())#第一个字母大写，其他字母小写
# print(str.swapcase())#大小写互转
# print(str.islower())#所有字母都是小写返回True
# print(str.upper())#所有转大写
# print(str.lower())#所有转小写
# print(str.startswith('h'))#判断字符串是否以指定字符开头bool类型
# 强制类型转换y = str(x) z = int(w) u = float(x) 显示类型 type(u)
# x = 654
# y = str(x)
# print(y+"dgvfh")
# %s string %d int 占位符 %l long %f float
# name = input()
# age = int(input())
# print("dhb%s,3dhewf%d040"%(name,age))
# 通过m.n控制数字宽度和精度 %5d宽度为5 [][][]11
# %5.2f 宽度为5 精度为小数点第二位 11.345 设置%7.2 结果为[][]11.35 四舍五入
# %.2f 不限制宽度限制精度小数点2位 11.345 设置%.2f 结果为11.35

# 元组 元组与列表一样，可以封装多个数据，但是元组一旦创建，就不能修改
# 元组定义：tuple = (1,2,3) 用小括号逗号隔开隔开各个数据，数据类型可以不同
t1 = (1,"hello",True) #多个元素
t2 = (1,) #一个元素必须有，否则就不是元组
#