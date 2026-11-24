from django.test import TestCase
from django.db import connection


class DatabaseTests(TestCase):

    def test_database_connection(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_required_tables_exist(self):
        tables = connection.introspection.table_names()

        required_tables = [
            'users',
            'profiles',
            'courses',
            'notes',
            'ai_messages',
            'password_reset_token',
        ]

        for table in required_tables:
            with self.subTest(table=table):
                self.assertIn(table, tables)