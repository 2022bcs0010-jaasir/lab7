import os
import json
import pickle
import pandas as pd

from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score


print("Name: Mohamed Jaasir Subair")
print("Roll no: 2022BCS0010")

os.makedirs("output/model", exist_ok=True)
os.makedirs("app/artifacts", exist_ok=True)


df = pd.read_csv("dataset/winequality-red.csv", sep=";")

X = df.drop("quality", axis=1)
y = df["quality"]

corr = X.corrwith(y).abs().sort_values(ascending=False)
top5_features = corr.index[:5]

print("Selected Features:", list(top5_features))

X_selected = X[top5_features]

X_train, X_test, y_train, y_test = train_test_split(
    X_selected, y, test_size=0.20, random_state=42
)

model = Ridge(alpha=0.5, fit_intercept=True)
model.fit(X_train, y_train)

pred = model.predict(X_test)
mse_exp01_fs = mean_squared_error(y_test, pred)
r2_exp01_fs = r2_score(y_test, pred)

print("LR-01 (Feature Selected) MSE:", mse_exp01_fs)
print("LR-01 (Feature Selected) R2 :", r2_exp01_fs)








with open("output/model/trained_model.pkl", "wb") as f:
    pickle.dump(model, f)

metrics = {
    "MSE": mse_exp01_fs,
    "R2": r2_exp01_fs
}

with open("app/artifacts/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)
