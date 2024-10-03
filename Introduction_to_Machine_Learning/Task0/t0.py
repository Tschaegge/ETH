import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import csv

df = pd.read_csv("train.csv")

df_list = df.values.tolist()

x = []
y = []

for item in df_list:
    y.append(item[1])
    x.append(item[2:])

x,y = np.array(x), np.array(y)

model = LinearRegression().fit(x, y)

test = pd.read_csv("test.csv")

test_list = test.values.tolist()

test_x = []

for item in test_list:
    test_x.append(item[1:])

print(np.mean(test_x[34]))
print(np.mean(test_x[768]))
print(np.mean(test_x[233]))

test_x = np.array(test_x)

test_y = model.predict(test_x)

with open('result.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["Id", "y"])
    i = 10000
    for a in test_y:
        writer.writerow([i, a])
        i = i + 1
