# MPIN Strength Checker

GITHUB LINK: https://github.com/bhavyaaaa08/mpin-checker/tree/main

This project is a secure, rule-based MPIN (Mobile PIN) strength checker built with Python, MySQL, and Streamlit. It analyzes both 4-digit and 6-digit MPINs to determine their strength based on:

- Commonly used PINs (based on public datasets)
- User-specific demographic patterns:
  - Date of Birth (self + spouse)
  - Wedding Anniversary
- Length and repetition patterns

It also stores the evaluation logs securely in a MySQL database for future reference, ensuring that MPIN changes for the same user are updated appropriately.

## Project Structure

```
Bhavya/
├── 4 digits pin/
│   ├── .env                    # MUST BE CREATED using the format below
│   ├── app.py                 # Streamlit UI for ease of use
│   ├── final_4.py             # Final Python file including all features
│   ├── common-pins.txt        # Self-curated 200 most common 4-digit PINs
│   ├── test_4digit.py         # 25+ test cases (TASK D)
│   ├── reason.py              # Displaying the reasons (TASK C)
│   ├── pin-demographics.py    # Adding demographics (TASK B)
│   ├── common-pin-checker.py  # Most basic common PINs checker (TASK A)
├── 6 digits pin/
│   ├── .env                    # MUST BE CREATED using the format below
│   ├── app.py                 # Streamlit UI for ease of use
│   ├── final_6.py             # Final Python file including all features
│   ├── common-pins.txt        # Self-curated 200 most common 6-digit PINs
│   ├── test_6digit.py         # 25+ test cases (TASK D)
│   ├── reason.py              # Displaying the reasons (TASK C)
│   ├── pin-demographics.py    # Adding demographics (TASK B)
│   ├── common-pin-checker.py  # Most basic common PINs checker (TASK A)
├── README.md                  # This file
```

## Features

- Evaluates MPIN strength based on rule-based logic (no ML model needed).
- Supports both 4-digit and 6-digit MPINs.
- Provides two fully interactive interfaces made using Streamlit: one for 4-digit PINs and one for 6-digit PINs.
- Validates against commonly used MPINs (based on [DataGenetics blog](https://www.datagenetics.com/blog/september32012/)).
- Detects weak MPINs formed from:
  - DOB (self or spouse)
  - Wedding anniversary
- Logs every submission into a MySQL database for audit/history.
- Uses `.env` to securely manage database credentials.
- **User ID Format**: User IDs are strictly 4-digit numbers (e.g., `1234`, `0001`), validated both in the application and test cases.
- ![image](https://github.com/user-attachments/assets/aa17e91c-f389-4112-bae6-e6452168d6d8)

- **Handles MPIN Updates**: If a user changes their MPIN, the system updates the existing record in the database for that `user_id`, ensuring only the latest MPIN and its evaluation are stored.
- ![image](https://github.com/user-attachments/assets/4382cc45-8749-4ead-b565-00d6d41d2218)


## Database Usage

![Screenshot 2025-05-26 150622](https://github.com/user-attachments/assets/14b5c777-3da0-4138-ba51-4f5148d4932e)


The project uses a MySQL database (`mpin_db`) to store MPIN evaluation logs. The `mpin_logs` table is designed to:

- **Log Every Submission**: Each time a user checks an MPIN, the system logs the `user_id`, `mpin`, `length`, `strength`, `reasons`, `dob_self`, `dob_spouse`, `anniversary`, and `timestamp`.
- **Handle MPIN Changes**: If a user with an existing `user_id` submits a new MPIN, the system updates the existing record using MySQL's `ON DUPLICATE KEY UPDATE` mechanism. This ensures:
  - The latest MPIN, strength, and reasons are stored.
  - Demographic data (`dob_self`, `dob_spouse`, `anniversary`) is updated if provided.
  - The `timestamp` is updated to reflect the latest submission.
- **Primary Key**: The `user_id` serves as the primary key, ensuring that each user has only one record in the database at any time.
- **Data Integrity**: The system validates that `user_id` is a 4-digit number and that MPINs are either 4 or 6 digits (depending on the system) before logging to the database.

### Example Database Workflow for MPIN Changes

1. **First Submission**:
   - User ID: `1234`
   - MPIN: `5678` (4-digit system)
   - Strength: `STRONG`
   - The system inserts a new record into `mpin_logs` with `user_id = '1234'`.

2. **MPIN Change**:
   - Same User ID: `1234`
   - New MPIN: `9012`
   - Strength: `STRONG`
   - The system updates the existing record for `user_id = '1234'` with the new MPIN, strength, reasons, and timestamp, preserving other fields like `dob_self` unless updated.

This ensures that the database always reflects the most recent MPIN for each user while maintaining a history of updates via the `timestamp`.

## Setup & Installation

1. **Clone or Extract ZIP**  
   Unzip the folder and navigate into the directory.

2. **Install Dependencies**  
   ```
   pip install streamlit mysql-connector-python python-dotenv
   ```

3. **Create `.env` File** (not included in ZIP)  
   Create a `.env` file in both `4 digits pin/` and `6 digits pin/` directories with the following format:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=mpin_db
   ```

4. **MySQL Table Setup (One-Time)**  
   Run the following SQL commands to set up the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS mpin_db;
   USE mpin_db;
   CREATE TABLE IF NOT EXISTS mpin_logs (
       user_id VARCHAR(255) PRIMARY KEY,
       mpin VARCHAR(10),
       length INT,
       strength VARCHAR(10),
       reason_json TEXT,
       dob_self DATE,
       dob_spouse DATE,
       anniversary DATE,
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```
   The system will automatically insert or update logs in this table when an MPIN is checked.

## How to Run

Navigate to either the `4 digits pin/` or `6 digits pin/` directory and run:
```
streamlit run app.py
```

This will launch the web interface. You'll be able to:
- Enter your 4-digit `user_id` (e.g., `1234`).
- Enter your MPIN (4 or 6 digits, depending on the system) and demographic details.
- View the MPIN strength and reasons for weakness (if any).
- Log the data securely into the database, updating the record if the `user_id` already exists.

## Test Cases

- Located in `test_4digit.py` (4-digit system) and `test_6digit.py` (6-digit system).
- ![Screenshot 2025-05-26 151656](https://github.com/user-attachments/assets/61808d51-81a3-4c22-a43a-ed2218372503)
- ![Screenshot 2025-05-26 152622](https://github.com/user-attachments/assets/f19f53f6-cd9b-4bb6-a6f2-ad8670aea1b1)
- Each file contains **25+ test scenarios** covering:
  - Common MPINs (e.g., `1234`, `123456`)
  - Demographic matches (DOB, spouse DOB, anniversary)
  - Strong/weak evaluations
  - Boundary conditions (short/long MPINs, invalid `user_id`)
  - Database connection errors
  - `user_id` validation (must be a 4-digit number)
- Run the tests from the respective directory:
  ```
  python -m unittest test-cases.py
  ```

## Why No ML Model?

- A rule-based system was chosen because:
  - The problem is deterministic and explainable.
  - ML adds unnecessary complexity with no real value for this use case.
  - Easier to maintain and reason about results.
  - Rules are 100% auditable, which is critical for security applications.

## Why No Prebuilt Local Database?

- The project is expected to run on the evaluator’s machine.
- `.env` and `CREATE TABLE` SQL ensure setup flexibility.
- This avoids conflicts with local database configurations.

## Additional Facts

- **Leading Zeros Support**: The system preserves leading zeros in both MPINs (e.g., `0123`) and `user_id` (e.g., `0001`), ensuring they are stored and displayed correctly.
- **Unicode Handling**: The system rejects `user_id` inputs with Unicode characters, as they must be strictly numeric.
- **Error Handling**: The application includes robust error handling for database connection failures, invalid inputs, and more, ensuring a smooth user experience.
- **Streamlit Warnings in Tests**: When running tests, you may see `ScriptRunContext` warnings from Streamlit. These are harmless and can be ignored, as the tests don’t rely on Streamlit’s UI—they call the underlying functions directly.

## Future Enhancements

- Add a dashboard tab with charts (e.g., percentage of weak PINs, most common reasons for weakness).
- Implement a multi-user history view to display all past MPIN evaluations for a given `user_id`.
- Allow PIN suggestions for stronger alternatives when a weak MPIN is detected.
- Add email-based authentication with hashed MPIN storage for enhanced security.
- Introduce a feature to export MPIN logs as a CSV for auditing purposes.
- Add support for additional demographic patterns, such as phone number digits or other significant dates.
- Implement a reset mechanism to allow users to clear their database record and start fresh.
- Add unit tests for edge cases like database timeouts or network failures.
