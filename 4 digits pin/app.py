import streamlit as st
import os
import datetime
from final_4 import evaluate_strength_and_reasons, log_to_database
from dotenv import load_dotenv
import mysql.connector

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

def load_common_pins(file_name="common_pins.txt"):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r') as file:
        return {line.strip() for line in file if len(line.strip()) == 4 and line.strip().isdigit()}

st.title("4-Digit MPIN Strength Checker")

mpin = st.text_input("Enter your 4-digit MPIN:")
common_pins = load_common_pins()

today = datetime.date.today()
min_date = datetime.date(1950, 1, 1)

user_id = st.text_input("Enter your User ID")

dob_self = st.date_input("Your Date of Birth (DOB):", value=None, min_value=min_date, max_value=today)
dob_spouse = st.date_input("Spouse's DOB:", value=None, min_value=min_date, max_value=today)
anniversary = st.date_input("Wedding Anniversary:", value=None, min_value=min_date, max_value=today)

if st.button("Check Strength"):
    if not user_id:
        st.error("User ID is required.")
    elif not mpin.isdigit() or len(mpin) != 4:
        st.error("MPIN must be exactly 4 digits.")
    else:
        strength, reasons = evaluate_strength_and_reasons(
            mpin,
            common_pins,
            dob_self.strftime("%d-%m-%Y") if dob_self else None,
            dob_spouse.strftime("%d-%m-%Y") if dob_spouse else None,
            anniversary.strftime("%d-%m-%Y") if anniversary else None
        )
        st.success(f"Strength: {strength}")
        st.write("Reasons:", reasons)
        try:
            load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
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
                mpin,
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
            if affected_rows == 1:
                st.success("New user data logged to database.")
            elif affected_rows == 2:
                st.success("User MPIN and details updated in the database.")
        except Exception as e:
            st.error(f"Database Logging Error: {e}")