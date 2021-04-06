import pandas as pd 
import numpy as np 
import creme 
from creme import linear_model
from creme.multiclass import OutputCodeClassifier
from creme import metrics
import dill

df = pd.read_csv("carsdata2.csv")
l1 = df["L1"].astype('int')
l2 = df["L2"].astype('int')
l3 = df["L3"].astype('int')
l4 = df["L4"].astype('int')
df_x = [l1, l2, l3, l4]
df_y = df["k"].astype('int')
df_p = df["p"].astype('int')

model1 = OutputCodeClassifier(
			classifier = linear_model.LogisticRegression(),
			code_size=4,
			seed=42
		)


print("training ..........")
for x,p in zip(df_x, df_y):
	model1.fit_one(x, p)

print("saving ............")
with open('online_ml.pkl', 'wb') as f:
	dill.dump(model1, f)

print("done")










# model1.fit_one(data_dict2, i)
# met1.update(i, k_pred)
# model2.fit_one(data_dict2, max_precent)
# met2.update(max_precent, p_pred)


# d = {
# 	'L1':l1_data,
# 	'L2':l2_data,
# 	'L3':l3_data,
# 	'L4':l4_data,
# 	'k':key,
# 	'p':per
# }
# df = pd.DataFrame(data=d)
# df.to_csv("carsdata.csv")
# print(f"metrics 1 : {met1}")
# print(f"metrics 2 : {met2}")
# save_model( model2)