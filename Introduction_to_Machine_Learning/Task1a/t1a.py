from distutils import errors
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
import csv
from statistics import mean

df = pd.read_csv("train.csv")

df_list = df.values.tolist()

x = []
y = []

for item in df_list: 
    y.append(item[0])
    x.append(item[1:])

x,y = np.array(x), np.array(y) #convert to np.array because of performance reasons

kf = KFold(n_splits=10, random_state=1, shuffle=True) #this gives us the cross validation indices later


results = [[] for _ in range(5)] #initializes the resulting error array

i_map = {0.1: 0, 1: 1, 10: 2, 100: 3, 200: 4} #map right lambda to list index

for train_index, test_index in kf.split(x):
     x_train, x_test = x[train_index], x[test_index]
     y_train, y_test = y[train_index], y[test_index]
     #print("TRAIN:", x_train, "TEST:", y_test)
     for i in [0.1, 1, 10, 100, 200]:
        model = Ridge(alpha=i, fit_intercept=False).fit(x_train, y_train) #train ridge model with the different lambdas/alphas
        model_predict = model.predict(x_test)
        model_error = mean_squared_error(model_predict, y_test)**0.5
        results[i_map[i]].append(model_error)

with open('result.csv', 'w') as f: #write the median of the errors to file result.csv
    writer = csv.writer(f)
    for a in results:
        writer.writerow([mean(a)])
    





