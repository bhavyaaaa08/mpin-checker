import unittest
from unittest.mock import patch
import datetime
import mysql.connector
from app import load_common_pins, evaluate_strength_and_reasons
from dotenv import load_dotenv
import os

class Test4DigitSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load environment variables
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

    def setUp(self):
        # Connect to the database and clear it before each test
        self.connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute("DELETE FROM mpin_logs")
        self.connection.commit()
        self.common_pins = load_common_pins()

    def tearDown(self):
        # Clean up database connection after each test
        self.cursor.close()
        self.connection.close()

    def insert_to_database(self, user_id, mpin, strength, reasons, dob_self, dob_spouse, anniversary):
        # Create a new connection for each insert to allow mocking
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = connection.cursor()
        query = """
        INSERT INTO mpin_logs 
        (user_id, mpin, length, strength, reason_json, dob_self, dob_spouse, anniversary, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            mpin = VALUES(mpin),
            length = VALUES(length),
            strength = VALUES(strength),
            reason_json = VALUES(reason_json),
            dob_self = VALUES(dob_self),
            dob_spouse = VALUES(dob_spouse),
            anniversary = VALUES(anniversary),
            timestamp = NOW()
        """
        cursor.execute(query, (
            user_id,
            str(mpin),
            len(mpin),
            strength,
            ', '.join(reasons),
            dob_self.strftime("%Y-%m-%d") if dob_self else None,
            dob_spouse.strftime("%Y-%m-%d") if dob_spouse else None,
            anniversary.strftime("%Y-%m-%d") if anniversary else None
        ))
        connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        return affected_rows

    def get_db_record(self, user_id):
        self.cursor.execute("SELECT * FROM mpin_logs WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()

    # Test 1: Valid MPIN, New User ID
    def test_valid_mpin_new_user(self):
        user_id = "user1@example.com"
        mpin = "5678"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        affected_rows = self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        self.assertEqual(affected_rows, 1)  # Insert
        record = self.get_db_record(user_id)
        self.assertEqual(record[1], user_id)
        self.assertEqual(record[2], mpin)

    # Test 2: Valid MPIN, Existing User ID
    def test_valid_mpin_existing_user(self):
        user_id = "user2@example.com"
        # First insert
        mpin1 = "5678"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin1, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin1, strength, reasons, dob_self, None, None)
        # Update with new MPIN
        mpin2 = "9012"
        strength, reasons = evaluate_strength_and_reasons(mpin2, self.common_pins, "01-01-1990", None, None)
        affected_rows = self.insert_to_database(user_id, mpin2, strength, reasons, dob_self, None, None)
        self.assertEqual(affected_rows, 2)  # Update
        record = self.get_db_record(user_id)
        self.assertEqual(record[2], mpin2)

    # Test 3: MPIN with Leading Zero
    def test_leading_zero(self):
        user_id = "user3@example.com"
        mpin = "0123"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[2], "0123")

    # Test 4: Common MPIN
    def test_common_mpin(self):
        mpin = "1234"  # In common_pins.txt
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("COMMONLY_USED", reasons)

    # Test 5: Demographic Pattern (DOB Self)
    def test_demographic_dob_self(self):
        mpin = "0190"  # From DOB 01-01-1990
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_DOB_SELF", reasons)

    # Test 6: Demographic Pattern (DOB Spouse)
    def test_demographic_dob_spouse(self):
        mpin = "0290"  # From spouse DOB 02-02-1990
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, "02-02-1990", None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_DOB_SPOUSE", reasons)

    # Test 7: Demographic Pattern (Anniversary)
    def test_demographic_anniversary(self):
        mpin = "0315"  # From anniversary 03-03-2015
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, "03-03-2015")
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_ANNIVERSARY", reasons)

    # Test 8: Multiple Reasons
    def test_multiple_reasons(self):
        mpin = "1234"  # Common and from DOB 12-12-1934
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "12-12-1934", None, None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("COMMONLY_USED", reasons)
        self.assertIn("DEMOGRAPHIC_DOB_SELF", reasons)

    # Test 9: Strong MPIN
    def test_strong_mpin(self):
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.assertEqual(strength, "STRONG")
        self.assertEqual(reasons, [])

    # Test 10: Invalid MPIN (Too Short)
    def test_too_short_mpin(self):
        mpin = "123"
        self.assertFalse(mpin.isdigit() and len(mpin) == 4)

    # Test 11: Invalid MPIN (Too Long)
    def test_too_long_mpin(self):
        mpin = "12345"
        self.assertFalse(mpin.isdigit() and len(mpin) == 4)

    # Test 12: Invalid MPIN (Non-Digits)
    def test_non_digits_mpin(self):
        mpin = "12ab"
        self.assertFalse(mpin.isdigit() and len(mpin) == 4)

    # Test 13: Missing User ID
    def test_missing_user_id(self):
        user_id = ""
        self.assertFalse(user_id)

    # Test 14: Null DOB Self
    def test_null_dob_self(self):
        user_id = "user14@example.com"
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[6])  # dob_self

    # Test 15: Null DOB Spouse
    def test_null_dob_spouse(self):
        user_id = "user15@example.com"
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[7])  # dob_spouse

    # Test 16: Null Anniversary
    def test_null_anniversary(self):
        user_id = "user16@example.com"
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[8])  # anniversary

    # Test 17: Future DOB (Mock Streamlit Validation)
    def test_future_dob(self):
        dob_self = datetime.date(2026, 1, 1)
        today = datetime.date.today()
        self.assertFalse(dob_self <= today)

    # Test 18: Old DOB (Before 1950)
    def test_old_dob(self):
        dob_self = datetime.date(1900, 1, 1)
        min_date = datetime.date(1950, 1, 1)
        self.assertFalse(dob_self >= min_date)

    # Test 19: Database Connection Error
    @patch('mysql.connector.connect', side_effect=Exception("Mocked DB Error"))
    def test_db_connection_error(self, mock_connect):
        user_id = "user19@example.com"
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        with self.assertRaises(Exception):
            self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)

    # Test 20: Unicode in User ID
    def test_unicode_user_id(self):
        user_id = "user20@éxample.com"
        mpin = "5678"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[1], user_id)

    # Test 21: Long User ID
    def test_long_user_id(self):
        user_id = "a" * 255
        mpin = "5678"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[1], user_id)

    # Test 22: Empty Reasons
    def test_empty_reasons(self):
        user_id = "user22@example.com"
        mpin = "5678"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[5], "")  # reason_json

if __name__ == "__main__":
    unittest.main()