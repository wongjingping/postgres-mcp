"""
Tests for the check_sql_injection function from main.py
"""
import unittest
from main import check_sql_injection


class TestCheckSQLInjection(unittest.TestCase):
    """Test cases for check_sql_injection function"""

    def test_safe_select_queries(self):
        """Test that safe SELECT queries return False"""
        safe_queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM products WHERE price > 100",
            "SELECT COUNT(*) FROM orders",
            "select * from customers",  # lowercase
            "   SELECT   id   FROM   table   ",  # extra whitespace
            "SELECT * FROM users WHERE name = 'delete'",  # delete as string value
            "SELECT * FROM users WHERE column_name = 'update_time'",  # update in column name
        ]
        
        for query in safe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertFalse(result, f"Query should be safe: {query}")

    def test_unsafe_delete_queries(self):
        """Test that DELETE queries return True"""
        unsafe_queries = [
            "DELETE FROM users",
            "DELETE FROM users WHERE id = 1",
            "delete from products",  # lowercase
            "   DELETE   FROM   table   ",  # extra whitespace
            "DELETE FROM users; SELECT * FROM passwords",  # compound query
            "SELECT * FROM passwords;DELETE FROM users;",  # compound query
        ]
        
        for query in unsafe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertTrue(result, f"Query should be unsafe: {query}")

    def test_unsafe_drop_queries(self):
        """Test that DROP queries return True"""
        unsafe_queries = [
            "DROP TABLE users",
            "DROP DATABASE mydb",
            "drop table products",  # lowercase
            "   DROP   TABLE   users   ",  # extra whitespace
            "DROP INDEX idx_name",
            "DROP TABLE users; SELECT * FROM passwords",  # compound query
            "SELECT * FROM passwords;DROP TABLE users;",  # compound query
        ]
        
        for query in unsafe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertTrue(result, f"Query should be unsafe: {query}")

    def test_unsafe_update_queries(self):
        """Test that UPDATE queries return True"""
        unsafe_queries = [
            "UPDATE users SET name = 'John'",
            "UPDATE products SET price = 100 WHERE id = 1",
            "update table set column = value",  # lowercase
            "   UPDATE   users   SET   name   =   'test'   ",  # extra whitespace
            "UPDATE users SET name = 'John'; SELECT * FROM passwords",  # compound query
            "SELECT * FROM passwords;UPDATE users SET name = 'John';",  # compound query
        ]
        
        for query in unsafe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertTrue(result, f"Query should be unsafe: {query}")

    def test_mixed_case_keywords(self):
        """Test keywords in different cases"""
        test_cases = [
            ("Delete FROM users", True),
            ("dElEtE FROM users", True),
            ("UPDATE users SET name = 'test'", True),
            ("uPdAtE users SET name = 'test'", True),
            ("Drop TABLE users", True),
            ("dRoP TABLE users", True),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertEqual(result, expected, f"Query: {query}")

    def test_compound_queries(self):
        """Test compound queries with multiple statements"""
        unsafe_queries = [
            "SELECT * FROM users; DELETE FROM users",
            "SELECT id FROM products; DROP TABLE products",
            "SELECT name FROM customers; UPDATE customers SET active = 0",
        ]
        
        for query in unsafe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertTrue(result, f"Compound query should be unsafe: {query}")

    def test_keywords_in_string_literals(self):
        """Test that keywords within string literals are treated as safe"""
        safe_queries = [
            "SELECT * FROM users WHERE description = 'This will delete records'",
            "SELECT * FROM logs WHERE action = 'DROP CONNECTION'",
            "SELECT * FROM audit WHERE message = 'UPDATE COMPLETED'",
            "SELECT 'delete' as action FROM users",
            "SELECT 'This contains DELETE keyword' FROM table",
            "SELECT 'This contains DROP keyword' FROM table",
            "SELECT 'This contains UPDATE keyword' FROM table",
        ]
        
        for query in safe_queries:
            with self.subTest(query=query):
                result = check_sql_injection(query)
                self.assertFalse(result, f"Query with keyword in string should be safe: {query}")

    def test_empty_and_whitespace_queries(self):
        """Test edge cases with empty or whitespace-only queries"""
        edge_cases = [
            ("", False),
            ("   ", False),
            ("\n\t  \n", False),
        ]
        
        for query, expected in edge_cases:
            with self.subTest(query=repr(query)):
                result = check_sql_injection(query)
                self.assertEqual(result, expected, f"Query: {repr(query)}")

    def test_complex_safe_queries(self):
        """Test complex but safe SELECT queries"""
        safe_queries = [
            """
            SELECT u.id, u.name, p.title 
            FROM users u 
            JOIN posts p ON u.id = p.user_id 
            WHERE u.active = true 
            ORDER BY p.created_at DESC 
            LIMIT 10
            """,
            """
            SELECT 
                COUNT(*) as total,
                AVG(price) as avg_price
            FROM products 
            WHERE category IN ('electronics', 'books')
            GROUP BY category
            """,
            "SELECT * FROM users WHERE email LIKE '%@example.com'",
        ]
        
        for query in safe_queries:
            with self.subTest(query=query.strip()):
                result = check_sql_injection(query)
                self.assertFalse(result, f"Complex SELECT should be safe: {query.strip()}")


if __name__ == '__main__':
    unittest.main() 