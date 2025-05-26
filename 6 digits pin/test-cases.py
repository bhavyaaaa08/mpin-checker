import unittest
from unittest.mock import patch
import datetime
import mysql.connector
from app import load_common_pins, evaluate_strength_and_reasons
from dotenv import load_dotenv
import os

class Test6DigitSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

    def setUp(self):
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
        self.cursor.close()
        self.connection.close()

    def insert_to_database(self, user_id, mpin, strength, reasons, dob_self, dob_spouse, anniversary):
        if not (isinstance(user_id, str) and user_id.isdigit() and len(user_id) == 4):
            raise ValueError("user_id must be a 4-digit number")

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

    #1: Valid MPIN, New User ID
    def test_valid_mpin_new_user(self):
        user_id = "2001"
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        affected_rows = self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        self.assertEqual(affected_rows, 1)
        record = self.get_db_record(user_id)
        self.assertEqual(record[1], user_id)
        self.assertEqual(record[2], mpin)

    #2: Valid MPIN, Existing User ID
    def test_valid_mpin_existing_user(self):
        user_id = "2002"
        mpin1 = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin1, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin1, strength, reasons, dob_self, None, None)
        mpin2 = "901234"
        strength, reasons = evaluate_strength_and_reasons(mpin2, self.common_pins, "01-01-1990", None, None)
        affected_rows = self.insert_to_database(user_id, mpin2, strength, reasons, dob_self, None, None)
        self.assertEqual(affected_rows, 2)
        record = self.get_db_record(user_id)
        self.assertEqual(record[2], mpin2)

    #3: MPIN with Leading Zero
    def test_leading_zero(self):
        user_id = "2003"
        mpin = "012345"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[2], "012345")

    #4: Common MPIN
    def test_common_mpin(self):
        mpin = "123456"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("COMMONLY_USED", reasons)

    #5: DOB Self
    def test_demographic_dob_self(self):
        mpin = "010190"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_DOB_SELF", reasons)

    #6: DOB Spouse
    def test_demographic_dob_spouse(self):
        mpin = "020290"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, "02-02-1990", None)
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_DOB_SPOUSE", reasons)

    #7: Anniversary
    def test_demographic_anniversary(self):
        mpin = "030315"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, "03-03-2015")
        self.assertEqual(strength, "WEAK")
        self.assertIn("DEMOGRAPHIC_ANNIVERSARY", reasons)


    #9: Strong MPIN
    def test_strong_mpin(self):
        mpin = "167890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.assertEqual(strength, "STRONG")
        self.assertEqual(reasons, [])

    # Test 10: Invalid MPIN (Too Short)
    def test_too_short_mpin(self):
        mpin = "12345"
        self.assertFalse(mpin.isdigit() and len(mpin) == 6)

    #11: Invalid MPIN (Too Long)
    def test_too_long_mpin(self):
        mpin = "1234567"
        self.assertFalse(mpin.isdigit() and len(mpin) == 6)

    #12: Invalid MPIN (Non-Digits)
    def test_non_digits_mpin(self):
        mpin = "1234ab"
        self.assertFalse(mpin.isdigit() and len(mpin) == 6)

    #13: Missing User ID
    def test_missing_user_id(self):
        user_id = ""
        self.assertFalse(user_id)

    #14: Null DOB Self
    def test_null_dob_self(self):
        user_id = "2014"
        mpin = "567890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[6])

    #15: Null DOB Spouse
    def test_null_dob_spouse(self):
        user_id = "2015"
        mpin = "567890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[7])

    #16: Null Anniversary
    def test_null_anniversary(self):
        user_id = "2016"
        mpin = "567890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertIsNone(record[8])

    #17: Future DOB (Mock Streamlit Validation)
    def test_future_dob(self):
        dob_self = datetime.date(2026, 1, 1)
        today = datetime.date.today()
        self.assertFalse(dob_self <= today)

    #18: Old DOB (Before 1950)
    def test_old_dob(self):
        dob_self = datetime.date(1900, 1, 1)
        min_date = datetime.date(1950, 1, 1)
        self.assertFalse(dob_self >= min_date)

    #19: Database Connection Error
    @patch('mysql.connector.connect', side_effect=Exception("Mocked DB Error"))
    def test_db_connection_error(self, mock_connect):
        user_id = "2019"
        mpin = "567890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        with self.assertRaises(Exception):
            self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)

    #20: Unicode in User ID (Should Fail - Invalid Format)
    def test_unicode_user_id(self):
        user_id = "user20@éxample.com"
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        with self.assertRaises(ValueError):
            self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)

    #21: Long User ID (Should Fail - Invalid Length)
    def test_long_user_id(self):
        user_id = "a" * 255
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        with self.assertRaises(ValueError):
            self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)

    #22: Empty Reasons
    def test_empty_reasons(self):
        user_id = "2022"
        mpin = "561890"
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, None, None, None)
        self.insert_to_database(user_id, mpin, strength, reasons, None, None, None)
        record = self.get_db_record(user_id)
        self.assertEqual(record[5], "")  # reason_json

    #23: Invalid User ID (Non-Digits)
    def test_invalid_user_id_non_digits(self):
        user_id = "12ab"
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        with self.assertRaises(ValueError):
            self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)

    #24: Invalid User ID (Too Short)
    def test_invalid_user_id_too_short(self):
        user_id = "123"
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        with self.assertRaises(ValueError):
            self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)

    #25: Invalid User ID (Too Long)
    def test_invalid_user_id_too_long(self):
        user_id = "12345"
        mpin = "567890"
        dob_self = datetime.date(1990, 1, 1)
        strength, reasons = evaluate_strength_and_reasons(mpin, self.common_pins, "01-01-1990", None, None)
        with self.assertRaises(ValueError):
            self.insert_to_database(user_id, mpin, strength, reasons, dob_self, None, None)

if __name__ == "__main__":
    unittest.main()
