from datetime import datetime
import os

def load_common_pins(file_name="common_pins.txt"):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r') as file:
        return {line.strip() for line in file if len(line.strip()) == 6 and line.strip().isdigit()}

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

    patterns.add(day + month + year_short)
    patterns.add(day + year_short + month)
    patterns.add(month + day + year_short)
    patterns.add(month + year_short + day)
    patterns.add(year_short + day + month)
    patterns.add(year_short + month + day)

    patterns.add(day * 3)
    patterns.add(month * 3)
    patterns.add(year_short * 3)

    patterns.add((day + month + year_short)[::-1])
    patterns.add((day + year_short + month)[::-1])
    patterns.add((month + day + year_short)[::-1])
    patterns.add((month + year_short + day)[::-1])
    patterns.add((year_short + day + month)[::-1])
    patterns.add((year_short + month + day)[::-1])

    patterns.add(year_full[2:] + month + day)
    patterns.add(year_full[2:] + day + month)
    patterns.add(month + year_full[2:] + day)
    patterns.add(day + year_full[2:] + month)

    patterns.add(month + day + year_full)
    patterns.add(day + month + year_full)
    patterns.add(month + day + year_short)
    patterns.add(day + month + year_short)

    patterns.add(day + month + year_short)
    patterns.add(day + month + year_short[:2])
    patterns.add(day + month + year_short[2:])

    return patterns

def get_valid_date(prompt):
    while True:
        date_input = input(prompt).strip()
        try:
            datetime.strptime(date_input, "%d-%m-%Y")
            return date_input
        except ValueError:
            print("Invalid date format. Please enter date as DD-MM-YYYY.")

def evaluate_strength_and_reasons(mpin, common_pins_set, dob_self, dob_spouse, anniversary):
    reasons = []

    if mpin in common_pins_set:
        reasons.append("COMMONLY_USED")

    if dob_self:
        dob_self_patterns = generate_demographic_patterns(dob_self)
        if mpin in dob_self_patterns:
            reasons.append("DEMOGRAPHIC_DOB_SELF")

    if dob_spouse:
        dob_spouse_patterns = generate_demographic_patterns(dob_spouse)
        if mpin in dob_spouse_patterns:
            reasons.append("DEMOGRAPHIC_DOB_SPOUSE")

    if anniversary:
        anniversary_patterns = generate_demographic_patterns(anniversary)
        if mpin in anniversary_patterns:
            reasons.append("DEMOGRAPHIC_ANNIVERSARY")

    strength = "STRONG" if not reasons else "WEAK"
    return strength, reasons

if __name__ == "__main__":
    common_pins = load_common_pins()

    mpin = input("Enter a 6-digit MPIN: ").strip()
    if not (mpin.isdigit() and len(mpin) == 6):
        print("Error: MPIN must be exactly 6 digits.")
        exit()

    dob_self = get_valid_date("Enter your DOB (DD-MM-YYYY): ")
    dob_spouse = get_valid_date("Enter spouse DOB (DD-MM-YYYY): ")
    anniversary = get_valid_date("Enter wedding anniversary (DD-MM-YYYY): ")

    strength, reasons = evaluate_strength_and_reasons(mpin, common_pins, dob_self, dob_spouse, anniversary)

    print("Strength:", strength)
    print("Reasons:", reasons)
