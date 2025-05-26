import os

def load_common_pins(file_name="common_pins.txt"):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r') as file:
        return {line.strip() for line in file if len(line.strip()) == 4 and line.strip().isdigit()}

def is_common_pin(mpin, common_pins_set):

    return mpin in common_pins_set

if __name__ == "__main__":
    common_pins = load_common_pins()

    mpin = input("Enter a 4-digit MPIN: ").strip()

    if not (mpin.isdigit() and len(mpin) == 4):
        print("Error: MPIN must be a 4-digit number.")
    elif is_common_pin(mpin, common_pins):
        print("Result: WEAK - COMMONLY USED PIN")
    else:
        print("Result: STRONG - NOT A COMMON PIN")
