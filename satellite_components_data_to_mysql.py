

import pandas as pd
import mysql.connector

# MySQL connection details
db_config = {
    "host":" 127.0.0.1",  # Change to '127.0.0.1' for local MySQL
    "user": "root",
    "password": "12345",
    "database": "SATELLITE_INVENTORY_SYSTEM",
    "port": 3306  # Adjust based on your database setup
}

# Establish connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Function to load CSV into MySQL
def load_csv_to_mysql(file_path, table_name):
    df = pd.read_csv(file_path)
    columns = ",".join(df.columns)

    for _, row in df.iterrows():
        values = ",".join(["%s"] * len(row))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        cursor.execute(sql, tuple(row))

    conn.commit()
    print(f"Data inserted into {table_name} successfully!")

# Load datasets
load_csv_to_mysql(r"C:\Users\D Janani\Downloads\inventory_unique.csv", "inventory")
load_csv_to_mysql(r"C:\Users\D Janani\Downloads\alternative_components (2).csv", "alternative_components")
load_csv_to_mysql(r"C:\Users\D Janani\Downloads\sales (1).csv", "sales")

# Close connection
cursor.close()
conn.close()




