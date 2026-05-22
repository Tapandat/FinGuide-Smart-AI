
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# ---------------- CONNECT DATABASE ----------------

conn = sqlite3.connect("finance.db")

# ---------------- LOAD EXPENSES ----------------

df = pd.read_sql_query(
    "SELECT * FROM expenses",
    conn
)

conn.close()

# ---------------- DEBUG OUTPUT ----------------

print(df.head())

print("Total Expenses:", len(df))

# ---------------- CHECK DATA ----------------

if len(df) < 5:

    print("❌ Add more expenses before training.")

else:

    # ---------------- CREATE FEATURES ----------------

    df['index'] = range(
        1,
        len(df) + 1
    )

    X = df[['index']]

    y = df['amount']

    # ---------------- TRAIN MODEL ----------------

    model = LinearRegression()

    model.fit(X, y)

    # ---------------- SAVE MODEL ----------------

    joblib.dump(
        model,
        "expense_prediction_model.pkl"
    )

    print("✅ Model Trained Successfully")
