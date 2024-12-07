import sqlite3

def connect_to_database(db_name):
    """Connect to the SQLite database and return the connection object."""
    try:
        conn = sqlite3.connect(db_name)
        print(f"Connected to database {db_name}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def print_motorcycles(conn):
    """Print all motorcycles from the bikes table."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bikes")
        rows = cursor.fetchall()
        print("Motorcycles in the database:")
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")

def main():
    db_name = 'bikes.db'
    conn = connect_to_database(db_name)
    if conn:
        print_motorcycles(conn)
        conn.close()

if __name__ == "__main__":
    main()