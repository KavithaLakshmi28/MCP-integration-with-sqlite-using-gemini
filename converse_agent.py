import sqlite3
import google.generativeai as genai
import os
import re

class ConverseAgent:
    def __init__(self, model_id=None):
        if model_id is None:
            model_id = os.getenv("MODEL_NAME", "gemini-pro")  # Use environment variable if not provided
        self.model = genai.GenerativeModel(model_id)
        self.messages = []
        self.db_path = os.getenv("DB_PATH", "/home/fidev9/Downloads/mcp_server_sqlite/MCPmikegc/amazon-bedrock-mcp/test.db")

    async def invoke_with_gemini(self, prompt):
        """Process user input using Gemini API and execute SQL queries if applicable."""
        self.messages.append({"role": "user", "content": prompt})
        response = self.model.generate_content(prompt)
        response_text = response.text.strip()  # Extract query from response

                # Extract SQL query using regex (to avoid extra text)
        sql_match = re.search(r"```sql\n(.*?)\n```", response_text, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            sql_query = response_text.strip()

        # Check for INSERT, UPDATE, DELETE → Commit changes
        if sql_query.lower().startswith(("insert", "update", "delete")):
            return self.execute_sql(sql_query, commit=True)  # Commit changes for write operations

        # Check for SELECT → Fetch data
        elif sql_query.lower().startswith("select"):
            return self.execute_sql(sql_query)  # Execute SELECT queries normally

        # If response is not SQL, return as is
        self.messages.append({"role": "assistant", "content": response.text})
        return response.text  

    def execute_sql(self, query, commit=False):
        """Execute SQL queries (SELECT, INSERT, UPDATE, DELETE) on SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)

                # Handle INSERT, UPDATE, DELETE with commit
                if commit:
                    conn.commit()
                    return "Query executed successfully and changes committed."

                # Handle SELECT statements
                rows = cursor.fetchall()
                if not rows:
                    return " No results found."

                # Fetch column names
                column_names = [desc[0] for desc in cursor.description]
                result = [dict(zip(column_names, row)) for row in rows]
                # return result
                
                # Convert the results into a readable table format
                formatted_output = self.format_results(column_names, result)
                return formatted_output

        except sqlite3.Error as e:
            return f"Database error: {str(e)}"
    
    def format_results(self, column_names, rows):
        """
        Format the SQL query results into a readable table format.
        """
        table = f"| {' | '.join(column_names)} |\n"  # Table header
        table += f"|{'-' * (len(table) - 3)}|\n"  # Table separator

        for row in rows:
            table += f"| {' | '.join(str(value) for value in row.values())} |\n"

        return table.strip()
        

