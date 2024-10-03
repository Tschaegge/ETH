import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import csv
import math
from sklearn.linear_model import LassoCV, Ridge

df = pd.read_csv("train.csv")

df_list = df.values.tolist()

x_in = []
y = []

for item in df_list:
    y.append(item[1])
    x_in.append(item[2:])

x = []
q = 0

for ll in x_in: #transform the features
    x.append([])
    
    for i in range(21):
        if i in [0, 1, 2, 3, 4]:
            x[q].append(ll[i])
        if i in [5,6,7,8,9]:
            x[q].append(ll[i-5]*ll[i-5])
        if i in [10,11,12,13,14]:
            x[q].append(math.exp(ll[i-10]))
        if i in [15, 16, 17, 18, 19]:
            x[q].append(math.cos(ll[i-15]))
        if i == 20:
            x[q].append(1)
    q = q + 1

x,y = np.array(x), np.array(y)

#x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.0, random_state=0) #split into test and train data

lasso = LassoCV(cv=5, random_state=0, fit_intercept=False, max_iter=2000).fit(x, y) #perform Lasso regularization with cross validation

with open('result.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for a in lasso.coef_:
        writer.writerow([a])

