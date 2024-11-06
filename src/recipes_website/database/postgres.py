import traceback

import psycopg2
from psycopg2 import sql


class PostgresDB:
    def __init__(self, host, database, user, password):
        """
        Initialize the connection to the PostgreSQL database.

        :param host: The host of the PostgreSQL server.
        :param database: The name of the PostgreSQL database.
        :param user: The user to connect to the PostgreSQL database.
        :param password: The password of the PostgreSQL user.
        """
        try:
            self.connection = psycopg2.connect(host=host, database=database, user=user, password=password)
            self.cursor = self.connection.cursor()
            print("Connection to PostgreSQL database established.")
        except Exception as e:
            print("Error connecting to PostgreSQL database:", e)
            traceback.print_exc()

    def create_table(self, table_name, columns):
        """
        Create a table in the PostgreSQL database.

        :param table_name: The name of the table to create.
        :param columns: A dictionary with column names and their types.
        Example:
        columns = {
            'id': 'SERIAL PRIMARY KEY',
            'name': 'VARCHAR(100)',
            'age': 'INTEGER'
        }
        """
        try:
            column_definitions = ", ".join([f"{col} {col_type}" for col, col_type in columns.items()])
            create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                sql.Identifier(table_name), sql.SQL(column_definitions)
            )
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print(f"Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error creating table '{table_name}':", e)
            traceback.print_exc()

    def insert_row(self, table_name, values):
        """
        Insert a row into a table.

        :param table_name: The name of the table to insert data into.
        :param values: A dictionary with column names as keys and corresponding values.
        Example:
        values = {
            'name': 'John Doe',
            'age': 30
        }
        """
        try:
            columns = ", ".join(values.keys())
            value_placeholders = ", ".join(["%s"] * len(values))
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name), sql.SQL(columns), sql.SQL(value_placeholders)
            )
            self.cursor.execute(insert_query, tuple(values.values()))
            self.connection.commit()
            print(f"Row inserted into '{table_name}' successfully.")
        except Exception as e:
            print(f"Error inserting row into '{table_name}':", e)
            traceback.print_exc()

    def delete_row(self, table_name, condition):
        """
        Delete a row from a table.

        :param table_name: The name of the table to delete data from.
        :param condition: The condition to match rows for deletion (e.g., "id = 1").
        """
        try:
            delete_query = sql.SQL("DELETE FROM {} WHERE {}").format(sql.Identifier(table_name), sql.SQL(condition))
            self.cursor.execute(delete_query)
            self.connection.commit()
            print(f"Row(s) deleted from '{table_name}' successfully.")
        except Exception as e:
            print(f"Error deleting row(s) from '{table_name}':", e)
            traceback.print_exc()

    def fetch_all(self, table_name):
        """
        Fetch all rows from a table.

        :param table_name: The name of the table to fetch data from.
        :return: A list of tuples containing the rows.
        """
        try:
            fetch_query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))
            self.cursor.execute(fetch_query)
            rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            print(f"Error fetching rows from '{table_name}':", e)
            traceback.print_exc()
            return []

    def fetch_one(self, table_name, condition):
        """
        Fetch a single row from a table based on a condition.

        :param table_name: The name of the table to fetch data from.
        :param condition: The condition to filter rows (e.g., "id = 1").
        :return: A tuple containing the row.
        """
        try:
            fetch_query = sql.SQL("SELECT * FROM {} WHERE {}").format(sql.Identifier(table_name), sql.SQL(condition))
            self.cursor.execute(fetch_query)
            row = self.cursor.fetchone()
            return row
        except Exception as e:
            print(f"Error fetching row from '{table_name}':", e)
            traceback.print_exc()
            return None

    def close_connection(self):
        """
        Close the connection to the PostgreSQL database.
        """
        try:
            self.cursor.close()
            self.connection.close()
            print("Connection to PostgreSQL database closed.")
        except Exception as e:
            print("Error closing the connection:", e)
            traceback.print_exc()


# Example usage:
if __name__ == "__main__":
    db = PostgresDB(host="localhost", database="xxx", user="postgres", password="xxx")

    # Create a new table
    columns = {"id": "SERIAL PRIMARY KEY", "name": "VARCHAR(100)", "age": "INTEGER"}
    db.create_table("persons", columns)

    # Insert a new row
    db.insert_row("persons", {"name": "Alice", "age": 28})

    # Fetch all rows
    rows = db.fetch_all("persons")
    print("Rows in persons table:", rows)

    # Fetch a single row
    row = db.fetch_one("persons", "name = 'Alice'")
    print("Fetched row:", row)

    # Delete a row
    db.delete_row("persons", "name = 'Alice'")

    # Close the connection
    db.close_connection()
