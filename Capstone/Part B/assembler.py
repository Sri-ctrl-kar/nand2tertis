
import sys
import re
from pathlib import Path


# ============================================================
# HACK ASSEMBLER
# Personal number K = 47
# Extra feature: Warn when a label is declared twice
# ============================================================


# ------------------------------------------------------------
# PREDEFINED SYMBOLS
# ------------------------------------------------------------

PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,
}

# Registers R0 to R15
for i in range(16):
    PREDEFINED_SYMBOLS[f"R{i}"] = i


# ------------------------------------------------------------
# COMPUTATION TABLE
# ------------------------------------------------------------

COMP_TABLE = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "M":   "1110000",

    "!D":  "0001101",
    "!A":  "0110001",
    "!M":  "1110001",

    "-D":  "0001111",
    "-A":  "0110011",
    "-M":  "1110011",

    "D+1": "0011111",
    "A+1": "0110111",
    "M+1": "1110111",

    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",

    "D+A": "0000010",
    "D+M": "1000010",

    "D-A": "0010011",
    "D-M": "1010011",

    "A-D": "0000111",
    "M-D": "1000111",

    "D&A": "0000000",
    "D&M": "1000000",

    "D|A": "0010101",
    "D|M": "1010101",
}


# ------------------------------------------------------------
# DESTINATION TABLE
# ------------------------------------------------------------

DEST_TABLE = {
    "":    "000",
    "M":   "001",
    "D":   "010",
    "MD":  "011",
    "A":   "100",
    "AM":  "101",
    "AD":  "110",
    "AMD": "111",
}


# ------------------------------------------------------------
# JUMP TABLE
# ------------------------------------------------------------

JUMP_TABLE = {
    "":    "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


# ------------------------------------------------------------
# CLEAN SOURCE CODE
# ------------------------------------------------------------

def clean_lines(filename):
    instructions = []

    with open(filename, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            # Remove comments
            line = line.split("//")[0]

            # Remove spaces and tabs
            line = "".join(line.split())

            if line:
                instructions.append((line, line_number))

    return instructions


# ------------------------------------------------------------
# FIRST PASS
# Identify labels and calculate their ROM addresses
# ------------------------------------------------------------

def first_pass(instructions):

    symbols = PREDEFINED_SYMBOLS.copy()

    rom_address = 0
    labels_seen = set()

    for instruction, line_number in instructions:

        if instruction.startswith("(") and instruction.endswith(")"):

            label = instruction[1:-1]

            if not re.fullmatch(r"[A-Za-z_.$:][A-Za-z0-9_.$:]*", label):
                raise ValueError(
                    f"Line {line_number}: invalid label '{label}'"
                )

            # K = 47, duplicate-label warning feature
            if label in labels_seen:
                print(
                    f"Warning: Line {line_number}: "
                    f"label '{label}' is declared more than once."
                )
                continue

            labels_seen.add(label)

            if label in symbols:
                print(
                    f"Warning: Line {line_number}: "
                    f"label '{label}' conflicts with an existing symbol."
                )
            else:
                symbols[label] = rom_address

        else:
            rom_address += 1

    return symbols


# ------------------------------------------------------------
# A-INSTRUCTION ENCODING
# ------------------------------------------------------------

def encode_a_instruction(instruction, symbols, next_variable, line_number):

    symbol = instruction[1:]

    if not symbol:
        raise ValueError(
            f"Line {line_number}: empty A-instruction"
        )

    if symbol.isdigit():

        address = int(symbol)

    else:

        if not re.fullmatch(r"[A-Za-z_.$:][A-Za-z0-9_.$:]*", symbol):
            raise ValueError(
                f"Line {line_number}: invalid symbol '{symbol}'"
            )

        if symbol not in symbols:

            if next_variable[0] > 32767:
                raise ValueError(
                    f"Line {line_number}: variable address overflow"
                )

            symbols[symbol] = next_variable[0]
            next_variable[0] += 1

        address = symbols[symbol]

    if not 0 <= address <= 32767:
        raise ValueError(
            f"Line {line_number}: address out of range '{symbol}'"
        )

    return format(address, "016b")


# ------------------------------------------------------------
# C-INSTRUCTION ENCODING
# ------------------------------------------------------------

def encode_c_instruction(instruction, line_number):

    if instruction.count("=") > 1 or instruction.count(";") > 1:
        raise ValueError(
            f"Line {line_number}: malformed C-instruction"
        )

    if "=" in instruction:

        dest, remaining = instruction.split("=", 1)

    else:

        dest = ""
        remaining = instruction

    if ";" in remaining:

        comp, jump = remaining.split(";", 1)

    else:

        comp = remaining
        jump = ""

    dest = dest.strip()
    comp = comp.strip()
    jump = jump.strip()

    # Accept destination letters in any valid order.
    # Examples: DM, MD, ADM, AMD.
    if (
        any(ch not in "ADM" for ch in dest)
        or len(set(dest)) != len(dest)
    ):
        raise ValueError(
            f"Line {line_number}: invalid destination '{dest}'"
        )

    # Convert to canonical order
    dest = "".join(ch for ch in "AMD" if ch in dest)

    if comp not in COMP_TABLE:
        raise ValueError(
            f"Line {line_number}: invalid computation '{comp}'"
        )

    if dest not in DEST_TABLE:
        raise ValueError(
            f"Line {line_number}: invalid destination '{dest}'"
        )

    if jump not in JUMP_TABLE:
        raise ValueError(
            f"Line {line_number}: invalid jump '{jump}'"
        )

    return (
        "111"
        + COMP_TABLE[comp]
        + DEST_TABLE[dest]
        + JUMP_TABLE[jump]
    )


# ------------------------------------------------------------
# SECOND PASS
# Translate assembly instructions into machine code
# ------------------------------------------------------------

def second_pass(instructions, symbols):

    machine_code = []

    # Variables start from RAM address 16
    next_variable = [16]

    for instruction, line_number in instructions:

        # Skip labels
        if instruction.startswith("(") and instruction.endswith(")"):
            continue

        if instruction.startswith("@"):

            binary = encode_a_instruction(
                instruction,
                symbols,
                next_variable,
                line_number
            )

        else:

            binary = encode_c_instruction(
                instruction,
                line_number
            )

        machine_code.append(binary)

    return machine_code


# ------------------------------------------------------------
# MAIN ASSEMBLER FUNCTION
# ------------------------------------------------------------

def assemble(filename):

    input_path = Path(filename)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {filename}"
        )

    if input_path.suffix.lower() != ".asm":
        raise ValueError(
            "Input file must have an .asm extension"
        )

    instructions = clean_lines(input_path)

    # First pass
    symbols = first_pass(instructions)

    # Second pass
    machine_code = second_pass(instructions, symbols)

    # Output file
    output_path = input_path.with_suffix(".hack")

    with open(output_path, "w", encoding="utf-8") as file:

        for binary in machine_code:
            file.write(binary + "\n")

    print("\nAssembly successful!")
    print(f"Input file: {input_path.name}")
    print(f"Output file: {output_path.name}")
    print(f"Instructions translated: {len(machine_code)}")


# ------------------------------------------------------------
# COMMAND-LINE INTERFACE
# ------------------------------------------------------------

def main():

    if len(sys.argv) != 2:

        print("Usage: python3 assembler.py <filename.asm>")
        sys.exit(1)

    filename = sys.argv[1]

    try:

        assemble(filename)

    except (ValueError, FileNotFoundError) as error:

        print(f"\nError: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
