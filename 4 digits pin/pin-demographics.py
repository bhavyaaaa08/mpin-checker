from datetime import datetime
import os

def load_common_pins(file_name="common_pins.txt"):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r') as file:
        return {line.strip() for line in file if len(line.strip()) == 4 and line.strip().isdigit()}
    

def generate_demographic_patterns(date_str):
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        return set()

    day = dt.strftime("%d")
    month = dt.strftime("%m")
    year_full = dt.strftime("%Y")
    year_short = dt.strftime("%y")

    patterns = set()

    patterns.add(day + month)
    patterns.add(month + day)
    patterns.add(day + year_short)
    patterns.add(year_short + day)
    patterns.add(month + year_short)
    patterns.add(year_short + month)

    patterns.add(year_short * 2)
    patterns.add(day * 2)
    patterns.add(month * 2)

    patterns.add(year_short + year_short[::-1])

    patterns.add((day + month)[::-1]) 
    patterns.add((month + day)[::-1]) 

    patterns.add(year_full[2:] + month)
    patterns.add(month + year_full[2:])

    return patterns

def is_common_pin(mpin, common_pins_set):
    return mpin in common_pins_set

def is_demographic_pin(mpin, dob_self, dob_spouse, anniversary):
    all_patterns = set()
    for date in [dob_self, dob_spouse, anniversary]:
        all_patterns.update(generate_demographic_patterns(date))
    return mpin in all_patterns

def evaluate_strength(mpin, common_pins_set, dob_self, dob_spouse, anniversary):
    if is_common_pin(mpin, common_pins_set):
        return "WEAK"
    if is_demographic_pin(mpin, dob_self, dob_spouse, anniversary):
        return "WEAK"
    return "STRONG"

def get_valid_date(prompt):
    while True:
        date_input = input(prompt).strip()
        try:
            datetime.strptime(date_input, "%d-%m-%Y")
            return date_input
        except ValueError:
            print("Invalid date format. Please enter date as DD-MM-YYYY.")

if __name__ == "__main__":
    common_pins = load_common_pins()

    mpin = input("Enter a 4-digit MPIN: ").strip()
    if not (mpin.isdigit() and len(mpin) == 4):
        print("Error: MPIN must be exactly 4 digits.")
        exit()

    dob_self = get_valid_date("Enter your DOB (DD-MM-YYYY): ")
    dob_spouse = get_valid_date("Enter spouse DOB (DD-MM-YYYY): ")
    anniversary = get_valid_date("Enter wedding anniversary (DD-MM-YYYY): ")

    strength = evaluate_strength(mpin, common_pins, dob_self, dob_spouse, anniversary)
    print("Strength:", strength)
