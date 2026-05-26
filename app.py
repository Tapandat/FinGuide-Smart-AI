import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px
import joblib
import numpy as np
import json
from email_service import send_email
from streamlit_oauth import OAuth2Component

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="FinGuide AI",
    page_icon="💰",
    layout="wide"
)

# ---------------- PROFESSIONAL CSS ----------------

st.markdown("""
<style>

/* Main App */
.stApp {
    background-color: #f4f7fb;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
    color: white;
}

/* Sidebar Text */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Main Titles */
h1 {
    color: #0f172a !important;
    font-weight: 700;
}

h2, h3, h4 {
    color: #1e293b !important;
}

/* Metric Cards */
[data-testid="metric-container"] {
    background-color: white;
    border: 1px solid #e2e8f0;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

/* Buttons */
.stButton > button {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #1d4ed8;
    color: white;
}

/* Input Fields */
.stTextInput input,
.stNumberInput input {
    border-radius: 10px;
    border: 1px solid #cbd5e1;
    padding: 10px;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------

def create_connection():
    return sqlite3.connect("finance.db")

# ---------------- USER FUNCTIONS ----------------

def register_user(username, email, password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    )
    try:
        cursor.execute(
            """
            INSERT INTO users(username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, hashed_password)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        stored_password = user[3]
        if bcrypt.checkpw(
            password.encode('utf-8'),
            stored_password
        ):
            return True
    return False

def get_user_email(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT email
        FROM users
        WHERE username=?
        """,
        (username,)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

# ---------------- EXPENSE FUNCTIONS ----------------

def add_expense(user_id, category, amount, note):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO expenses(user_id, category, amount, note)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, category, amount, note)
    )
    conn.commit()
    conn.close()

def load_expenses(user_id):
    conn = create_connection()
    query = f"""
    SELECT * FROM expenses
    WHERE user_id='{user_id}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------- INCOME FUNCTIONS ----------------

def add_income(user_id, source, amount):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO income(user_id, source, amount)
        VALUES (?, ?, ?)
        """,
        (user_id, source, amount)
    )
    conn.commit()
    conn.close()

def load_income(user_id):
    conn = create_connection()
    query = f"""
    SELECT * FROM income
    WHERE user_id='{user_id}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------- GOOGLE OAUTH CONSTANTS ----------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPE = "openid email profile"

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- AUTH SCREEN ----------------

if not st.session_state.logged_in:

    st.title("💰 FinGuide AI")

    auth_mode = st.sidebar.selectbox(
        "Authentication",
        ["Login", "Register", "Login with Google"]
    )

    # ---------------- GOOGLE LOGIN ----------------

    if auth_mode == "Login with Google":

        st.markdown("#### Sign in with Google")

        oauth2 = OAuth2Component(
            client_id=st.secrets["google_oauth"]["client_id"],
            client_secret=st.secrets["google_oauth"]["client_secret"],
            authorize_endpoint=GOOGLE_AUTH_URL,
            token_endpoint=GOOGLE_TOKEN_URL,
        )

        result = oauth2.authorize_button(
            name="Continue with Google",
            redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
            scope=GOOGLE_SCOPE,
            icon="https://www.google.com/favicon.ico",
            use_container_width=True,
            pkce="S256",
        )

        if result and "token" in result:

            import requests

            token = result["token"]["access_token"]

            user_info = requests.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token}"}
            ).json()

            google_email = user_info.get("email")
            google_name = user_info.get("name", google_email)

            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email=?",
                (google_email,)
            )
            existing = cursor.fetchone()

            if not existing:
                cursor.execute(
                    "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
                    (google_name, google_email, b"GOOGLE_OAUTH")
                )
                conn.commit()

            conn.close()

            st.session_state.logged_in = True
            st.session_state.username = google_name
            st.rerun()

    # ---------------- MANUAL REGISTER ----------------

    elif auth_mode == "Register":

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            success = register_user(username, email, password)
            if success:
                st.success("Registration Successful ✅")
            else:
                st.error("Username already exists")

    # ---------------- MANUAL LOGIN ----------------

    else:

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            success = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ---------------- MAIN APP ----------------

else:

    st.sidebar.title("💰 FinGuide AI")

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Income Manager",
            "Expense Entry",
            "Analytics",
            "Budget Planner",
            "Predictions",
            "Settings"
        ]
    )

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ---------------- CURRENT USER ----------------

    current_user = st.session_state.username

    # ---------------- LOAD DATA ----------------

    expense_df = load_expenses(current_user)
    income_df = load_income(current_user)

    total_income = (
        income_df['amount'].sum()
        if not income_df.empty else 0
    )

    total_expense = (
        expense_df['amount'].sum()
        if not expense_df.empty else 0
    )

    savings = total_income - total_expense

    # ---------------- DASHBOARD ----------------

    if menu == "Dashboard":

        st.title("💰 FinGuide AI Dashboard")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Income", f"₹{total_income}")
        col2.metric("Total Expenses", f"₹{total_expense}")
        col3.metric("Savings", f"₹{savings}")

        st.markdown("---")

        if total_income > 0:
            ratio = (savings / total_income) * 100
        else:
            ratio = 0

        st.subheader("Financial Health")

        if ratio >= 40:
            st.success("Excellent 🟢")
        elif ratio >= 20:
            st.warning("Good 🟡")
        else:
            st.error("Poor 🔴")

        if not expense_df.empty:

            category_data = expense_df.groupby(
                'category'
            )['amount'].sum().reset_index()

            fig = px.pie(
                category_data,
                names='category',
                values='amount',
                hole=0.4
            )

            st.plotly_chart(fig, use_container_width=True)

    # ---------------- INCOME MANAGER ----------------

    elif menu == "Income Manager":

        st.title("💵 Income Manager")

        source = st.selectbox(
            "Income Source",
            [
                "Salary",
                "Freelancing",
                "Investments",
                "Business",
                "Other"
            ]
        )

        amount = st.number_input("Income Amount", min_value=0.0)

        if st.button("Add Income"):
            add_income(current_user, source, amount)
            st.success("Income Added Successfully ✅")

        st.subheader("Income History")
        st.dataframe(income_df)

    # ---------------- EXPENSE ENTRY ----------------

    elif menu == "Expense Entry":

        st.title("➕ Add Expense")

        category = st.selectbox(
            "Category",
            [
                "Food",
                "Transport",
                "Bills",
                "Entertainment",
                "Healthcare",
                "Education",
                "Shopping"
            ]
        )

        amount = st.number_input("Expense Amount", min_value=0.0)
        note = st.text_input("Note")

        if st.button("Save Expense"):
            add_expense(current_user, category, amount, note)
            st.success("Expense Added Successfully ✅")

    # ---------------- ANALYTICS ----------------

    elif menu == "Analytics":

        st.title("📊 Financial Analytics")

        if not expense_df.empty:

            category_data = expense_df.groupby(
                'category'
            )['amount'].sum().reset_index()

            fig = px.bar(
                category_data,
                x='category',
                y='amount',
                text='amount',
                color='category'
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Expense History")
            st.dataframe(expense_df)

        else:
            st.info("No expense data available.")

    # ---------------- BUDGET PLANNER ----------------

    elif menu == "Budget Planner":

        st.title("💵 Budget Planner")

        monthly_budget = st.number_input("Monthly Budget", min_value=0.0)

        remaining = monthly_budget - total_expense

        st.metric("Remaining Budget", f"₹{remaining}")

        if total_expense > monthly_budget:
            st.error("Budget Exceeded ⚠️")
        elif total_expense > monthly_budget * 0.8:
            st.warning("80% Budget Used")
        else:
            st.success("Budget Under Control ✅")

    # ---------------- PREDICTIONS ----------------

    elif menu == "Predictions":

        st.title("🤖 AI Predictions")

        try:
            model = joblib.load("expense_prediction_model.pkl")
            future_days = st.slider("Future Days", 1, 30, 7)
            future = np.array([[len(expense_df) + future_days]])
            prediction = model.predict(future)
            st.success(f"Predicted Expense: ₹{prediction[0]:.2f}")
        except:
            st.warning("Train ML model first.")

    # ---------------- SETTINGS ----------------

    elif menu == "Settings":

        st.title("📧 Monthly Financial Reports")

        user_email = get_user_email(current_user)

        st.write(f"Registered Email: {user_email}")

        if st.button("Send Monthly Report"):

            report = f"""
FinGuide AI - Monthly Financial Summary

---------------------------------------

Total Income: ₹{total_income}

Total Expenses: ₹{total_expense}

Total Savings: ₹{savings}

---------------------------------------
"""

            if total_income > 0:
                ratio = (savings / total_income) * 100
            else:
                ratio = 0

            if ratio >= 40:
                report += "\nFinancial Health: Excellent"
            elif ratio >= 20:
                report += "\nFinancial Health: Good"
            else:
                report += "\nFinancial Health: Poor"

            report += "\n\nAI Recommendations:\n"

            if total_expense > total_income * 0.8:
                report += "- Reduce monthly spending.\n"
            else:
                report += "- Budget is under control.\n"

            report += "- Continue tracking expenses regularly.\n"

            send_email(
                user_email,
                "FinGuide AI Monthly Report",
                report
            )

            st.success("Financial Report Sent Successfully ✅")
