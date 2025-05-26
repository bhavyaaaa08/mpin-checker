import os

def load_common_pins(file_name="common_pins.txt"):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r') as file:
        return {line.strip() for line in file if len(line.strip()) == 6 and line.strip().isdigit()}

def is_common_pin(pin, common_pins):

    return pin in common_pins


if __name__ == "__main__":
    common_pins_6digit = load_common_pins('C:\\Users\\nanaj\\OneDrive - Manipal University Jaipur\\Documents\\Bhavya\\6 digit pin\\common-pins.txt')
    
    test_pin = input("Enter 6-digit MPIN: ").strip()
    
    if len(test_pin) != 6 or not test_pin.isdigit():
        print("Error: MPIN must be a 6-digit number.")
    else:
        if is_common_pin(test_pin, common_pins_6digit):
            print("Result: WEAK - COMMONLY USED PIN")
        else:
            print("Result: STRONG - NOT A COMMON PIN")
