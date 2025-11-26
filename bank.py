import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# ------------------------------
# Database Connection
# ------------------------------
DB_PATH = "customer_data"

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()

# ------------------------------
# Helper: Run SQL Query
# ------------------------------
def run_query(query, params=None):
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return pd.DataFrame()

# ------------------------------
# Sidebar Navigation
# ------------------------------
st.sidebar.title("BanksLight Dashboard")
menu = st.sidebar.radio("Navigate", [
    "🏠 Home", 
    "📊 SQLite Queries", 
    "📁 View Tables", 
    "🛠 CRUD Operations", 
    "📈 Charts", 
    "👨‍💼 Creator Info"
])

# ------------------------------
# HOME PAGE
# ------------------------------
if menu == "🏠 Home":
    st.title("🏦 BanksLight Analytics Dashboard")
    st.write("""
        Welcome to **BanksLight**, an interactive banking insights dashboard built with **Streamlit**.

        Features:
        - Analyze customer behaviour
        - Explore accounts and transactions
        - Run live SQLite queries
        - Perform CRUD operations
        - Visualize charts
    """)

# ------------------------------
# VIEW TABLES
# ------------------------------
elif menu == "📁 View Tables":
    st.title("📁 View Database Tables")

    tables = ["customers", "accounts", "transactions", "loans", "credit_cards", "branches", "support_tickets"]
    choice = st.selectbox("Select Table", tables)

    df = run_query(f"SELECT * FROM {choice}")
    st.dataframe(df, use_container_width=True)

# ------------------------------
# SQLITE QUERIES
# ------------------------------
elif menu == "📊 SQLite Queries":
    st.title("📊 Run SQLite Insights Queries")

    queries = {
        "1. How many customers exist per city, and what is their average account balance?":
                """SELECT city, COUNT(*) AS customers, 
               AVG(account_balance) AS avg_balance
               FROM customers c
               JOIN accounts a USING (customer_id)
               GROUP BY city LIMIT 5;""" ,

        "2. Which account type holds the highest total balance?": 
                """SELECT 
               c.account_type,
               SUM(a.account_balance) AS total_balance
               FROM customers c
               JOIN accounts a 
               ON c.customer_id = a.customer_id
               GROUP BY c.account_type
               ORDER BY total_balance DESC;""",

        "3. Top 10 customers by total balance across all accounts":
                 """SELECT 
               c.customer_id,
               c.name,
               c.city,
               c.account_type,
               SUM(a.account_balance) AS total_balance
               FROM customers c
               JOIN accounts a 
               ON c.customer_id = a.customer_id
               GROUP BY c.customer_id, c.name, c.city, c.account_type
               ORDER BY total_balance DESC
               LIMIT 5;""",

        "4. Customers who opened accounts in 2023 with balance > ₹1,00,000":
                """SELECT 
               c.customer_id,
               c.name,
               c.city,
               c.account_type,
               a.account_balance,
               c.join_date
               FROM customers c
               JOIN accounts a 
               ON c.customer_id = a.customer_id
               WHERE strftime('%Y', c.join_date) = '2023'
               AND a.account_balance > 100000
               ORDER BY a.account_balance DESC LIMIT 5;""",

        "5. Total transaction volume by transaction type":
                """SELECT txn_type, SUM(amount) AS total_transaction_volume
               FROM transactions
               GROUP BY txn_type
               ORDER BY total_transaction_volume DESC;""",

        "6. Accounts with more than 3 failed transactions in a month":
                """SELECT customer_id,
                strftime('%Y-%m', txn_time) AS txn_month,
                COUNT(*) AS failed_txn_count
               FROM transactions
               WHERE status = 'failed'
               GROUP BY customer_id, txn_month
               HAVING COUNT(*) > 2
               ORDER BY failed_txn_count DESC LIMIT 5;""",
        
        "7. Top 5 branches by transaction volume (last 6 months)":
                """SELECT b.Branch_Name,
                SUM(t.amount) AS total_transaction_volume
               FROM transactions t
               JOIN customers c ON t.customer_id = c.customer_id
               JOIN branches b ON c.city = b.City
               WHERE t.txn_time >= strftime('%Y-%m-%d', 'now', '-6 months')
               GROUP BY b.Branch_Name
               ORDER BY total_transaction_volume DESC LIMIT 5;""",

        "8. Accounts with 5+ high-value transactions (₹95,000+)":
            """SELECT customer_id, COUNT(txn_id) AS high_value_transaction_count
               FROM transactions
               WHERE amount >= 95000 AND status = 'success'
               GROUP BY customer_id
               HAVING COUNT(txn_id) >= 5
               ORDER BY high_value_transaction_count DESC LIMIT 5;""",

        "9. Avg loan amount & interest rate by loan type":
            """SELECT Loan_Type,
                      AVG(Loan_Amount) AS avg_loan_amount,
                      AVG(Interest_Rate) AS avg_interest_rate
               FROM loans
               GROUP BY Loan_Type
               ORDER BY avg_loan_amount DESC;""",

        "10. Customers holding more than one active loan":
            """SELECT Customer_ID,
                      COUNT(*) AS active_loans
               FROM loans
               WHERE Loan_Status IN ('Active', 'Approved')
               GROUP BY Customer_ID
               HAVING COUNT(*) > 1
               ORDER BY active_loans DESC LIMIT 5;""",

        "11. Top 5 customers with highest outstanding loan amount":
            """SELECT Customer_ID,
                      SUM(Loan_Amount) AS total_outstanding
               FROM loans
               WHERE Loan_Status != 'Closed'
               GROUP BY Customer_ID
               ORDER BY total_outstanding DESC LIMIT 5;""",

        "12. Branch with highest account balance":
            """SELECT b.Branch_Name,
                      SUM(a.account_balance) AS total_balance
               FROM accounts a
               JOIN customers c ON a.customer_id = c.customer_id
               JOIN branches b ON c.city = b.City
               GROUP BY b.Branch_Name
               ORDER BY total_balance DESC LIMIT 5;""",

        "13. Branch performance (customers, loans, transactions)":
            """SELECT b.Branch_Name,
                      COUNT(DISTINCT c.customer_id) AS total_customers,
                      COUNT(DISTINCT l.Loan_ID) AS total_loans,
                      SUM(t.amount) AS total_transaction_volume
               FROM branches b
               LEFT JOIN customers c ON c.city = b.City
               LEFT JOIN loans l ON l.Branch = b.Branch_Name
               LEFT JOIN transactions t ON t.customer_id = c.customer_id
               GROUP BY b.Branch_Name;""",

        "14. Issue categories with longest resolution time":
            """SELECT issue_category,
                      AVG(JULIANDAY(date_closed) - JULIANDAY(date_opened)) AS avg_resolution_days
               FROM support_tickets
               WHERE date_opened IS NOT NULL
               GROUP BY issue_category
               ORDER BY avg_resolution_days DESC;""",

        "15. Agents resolving most critical tickets with rating ≥ 4":
            """SELECT Support_Agent,
                      COUNT(*) AS resolved_critical_high_rating
               FROM support_tickets
               WHERE priority = 'Critical'
                 AND Customer_Rating >= 4
                 AND status = 'Resolved'
               GROUP BY Support_Agent
               ORDER BY resolved_critical_high_rating DESC;""",
        "16. How many customers exist in each city?":
            """SELECT city, COUNT(*) AS total_customers
            FROM customers
            GROUP BY city;
            """,
        "17. What is the average account balance by account type?":
            """SELECT account_type, AVG(account_balance) AS avg_balance
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            GROUP BY account_type;""",

        "18. Who are the top 10 customers by total account balance?":
            """SELECT c.name, SUM(a.account_balance) AS total_balance
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            GROUP BY c.customer_id
            ORDER BY total_balance DESC
            LIMIT 10;""",

        "19. Which customers opened accounts in 2023 with balance > ₹1,00,000?":
            """SELECT c.customer_id, c.name, a.account_balance
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            WHERE strftime('%Y', c.join_date) = '2023'
            AND a.account_balance > 100000;""",

        "20. Total transaction volume by transaction type":
            """SELECT txn_type, SUM(amount) AS total_volume
            FROM transactions
            GROUP BY txn_type;""",

        "21.Support agents who resolved most critical tickets with rating ≥ 4":
            """SELECT 
            support_agent,
            COUNT(*) AS resolved_tickets
            FROM tickets
            WHERE priority = 'Critical'
            AND customer_rating >= 4
            AND status = 'Resolved'
            GROUP BY support_agent
            ORDER BY resolved_tickets DESC;
            """,

        "22. Retrieve all customers who have not updated their account balance in the last 30 days.":
             """SELECT *
            FROM accounts
            WHERE last_updated < DATE('now', '-30 days');
            """,

        "23. Find the average age of customers for each account type.":
            """SELECT account_type, AVG(age) AS avg_age
            FROM customers
            GROUP BY account_type;
            """,

        "24. Count how many transactions happened on weekends.":
            """SELECT COUNT(*) AS weekend_transactions
            FROM transactions
            WHERE strftime('%w', txn_time) IN ('0','6');
            """,

        "25. Find customers who made at least one transaction above ₹50,000.":
            """SELECT DISTINCT customer_id
            FROM transactions
            WHERE amount > 50000;
            """,

        "26. Get the total number of failed transactions per customer.":
            """SELECT customer_id, COUNT(*) AS failed_count
            FROM transactions
            WHERE status = 'failed'
            GROUP BY customer_id;
            """,

        "7. Find the 10 earliest registered customers.":
            """SELECT *
            FROM customers
            ORDER BY join_date
            LIMIT 10;
            """,

        "28. Retrieve customers who live in the same city as more than 2 other customers.":
            """SELECT city, COUNT(*) AS num_customers
            FROM customers
            GROUP BY city
            HAVING num_customers > 2;
            """,

        "29. Find the count of transactions by status (success/failed).":
            """SELECT status, COUNT(*) AS count
            FROM transactions
            GROUP BY status;
            """,

        "30. Show customers whose name starts with 'A'.":
            """SELECT *
            FROM customers
            WHERE name LIKE 'A%';
            """
    }

    selected = st.selectbox("Choose a query", list(queries.keys()))

    if st.button("Run Query"):
        df = run_query(queries[selected])
        st.dataframe(df, use_container_width=True)

# ------------------------------
# CRUD OPERATIONS
# ------------------------------
elif menu == "🛠 CRUD Operations":
    st.title("🛠 CRUD Operations for Customers")

    action = st.radio("Select Action", ["Create", "Read", "Update", "Delete"])

    # CREATE
    if action == "Create":
        st.subheader("Add New Customer")
        cid = st.text_input("Customer ID")
        name = st.text_input("Name")
        gender = st.text_input("Gender")
        age = st.number_input("Age", min_value=1, max_value=120)
        city = st.text_input("City")
        account_type = st.text_input("Account Type")

        if st.button("Add Customer"):
            try:
                conn.execute("INSERT INTO customers VALUES (?,?,?,?,?,?, DATE('now'))", (cid, name, gender, age, city, account_type))
                conn.commit()
                st.success("Customer added successfully!")
            except Exception as e:
                st.error(e)

    # READ
    elif action == "Read":
        st.subheader("All Customers")
        df = run_query("SELECT * FROM customers")
        st.dataframe(df)

    # UPDATE
    elif action == "Update":
        st.subheader("Update Customer City")
        cid = st.text_input("Customer ID to Update")
        new_city = st.text_input("New City")

        if st.button("Update"):
            conn.execute("UPDATE customers SET city=? WHERE customer_id=?", (new_city, cid))
            conn.commit()
            st.success("Customer updated!")

    # DELETE
    elif action == "Delete":
        st.subheader("Delete Customer")
        cid = st.text_input("Customer ID to Delete")

        if st.button("Delete"):
            conn.execute("DELETE FROM customers WHERE customer_id=?", (cid,))
            conn.commit()
            st.success("Customer deleted!")

# ------------------------------
# CHARTS
# ------------------------------
elif menu == "📈 Charts":
    st.title("📈 Data Visualizations")

    chart_type = st.selectbox("Select Chart", [
        "Customers by City", 
        "Transaction Volume by Type", 
        "Account Balance Distribution"
    ])

    if chart_type == "Customers by City":
        df = run_query("SELECT city, COUNT(*) AS total FROM customers GROUP BY city")
        fig = px.bar(df, x="city", y="total", title="Customers by City")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Transaction Volume by Type":
        df = run_query("SELECT txn_type, SUM(amount) AS total FROM transactions GROUP BY txn_type")
        fig = px.pie(df, names="txn_type", values="total", title="Transaction Volume by Type")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Account Balance Distribution":
        df = run_query("SELECT account_balance FROM accounts")
        fig = px.histogram(df, x="account_balance", title="Account Balance Distribution")
        st.plotly_chart(fig, use_container_width=True)


# ------------------------------
# CREATOR INFO
# ------------------------------
elif menu == "👨‍💼 Creator Info":
    st.title("👨‍💼 Creator Information")
    st.write("""
    **Created By:** Ajay Pandey

    **Project:** BanksLight - Streamlit Banking Dashboard
             
    **Skills:** Python, SQL, Data Analysis,Streamlit, Pandas  

    **Features Implemented:**
    - Navigation Sidebar
    - SQLite Query Runner
    - CRUD Operations
    - Data Viewer
    - Charts
    - Modular Code
    """)
