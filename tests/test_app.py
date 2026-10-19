import unittest
import sqlite3
import os


class TestLaundryDatabase(unittest.TestCase):

    def test_database_connection(self):
        connection = sqlite3.connect(":memory:")
        self.assertIsNotNone(connection)
        connection.close()

    def test_database_query(self):
        connection = sqlite3.connect(":memory:")
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        connection.close()

    def test_laundry_order_status(self):
        valid_statuses = [
            "Pending",
            "Washing",
            "Drying",
            "Ironing",
            "Completed"
        ]
        self.assertIn("Washing", valid_statuses)
        self.assertIn("Completed", valid_statuses)

    def test_project_file_exists(self):
        self.assertTrue(os.path.exists("app.py"))


if __name__ == "__main__":
    unittest.main()