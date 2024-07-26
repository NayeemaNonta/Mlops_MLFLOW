"""
Shows autologging
"""

#Import libraries
import mlflow
import mlflow.sklearn
import pandas as pd
import argparse
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error



# ---DATA---
# Define column names
column_names = [
    'CRIM', 'ZN', 'INDUS', 'CHAS', 'NOX', 'RM', 'AGE', 'DIS', 'RAD', 'TAX', 
    'PTRATIO', 'B', 'LSTAT', 'MEDV'
]

# Load dataset
data = pd.read_csv("https://raw.githubusercontent.com/jbrownlee/Datasets/master/housing.csv", header=None, names=column_names)

# Features and target variable
X = data.iloc[:, :-1]  # All columns except the last one
y = data.iloc[:, -1]   # Last column

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


#---- INPUT ARGS ---
parser = argparse.ArgumentParser()
parser.add_argument('--n_estimators', type=int, default=100, help='Number of trees in the forest.')
parser.add_argument('--max_depth', type=int, default=10, help='Maximum depth of the tree.')
args = parser.parse_args()


# ENABLE AUTOLOGGING
mlflow.sklearn.autolog()


# Start an MLflow run
with mlflow.start_run():
    # Define the model
    model = RandomForestRegressor(n_estimators=args.n_estimators, max_depth=args.max_depth, random_state=42)

    # Train the model
    model.fit(X_train, y_train)

    # Predict
    train_predictions = model.predict(X_train)
    test_predictions = model.predict(X_test)

    # Evaluate the model
    train_rmse = root_mean_squared_error(y_train, train_predictions)
    test_rmse = root_mean_squared_error(y_test, test_predictions)
    
    print(f"Train RMSE: {train_rmse}")
    print(f"Test RMSE: {test_rmse}")

"""
python mlflow_autologging.py --n_estimators 200 --max_depth 15

"""
