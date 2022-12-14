import os
import sys

class SymbolTable:
    def __init__(self):
        # Create the pre-defined symbol table.
        self.table = {
            "R0": 0,
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5,
            "R6": 6,
            "R7": 7,
            "R8": 8,
            "R9": 9,
            "R10": 10,
            "R11": 11,
            "R12": 12,
            "R13": 13,
            "R14": 14,
            "R15": 15,
            "SCREEN": 16384,
            "KBD": 24576,
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4
        }

    def addEntry(self, symbol: str, value: int) -> None:
        self.table[symbol] = value

    def contains(self, symbol: str) -> bool:
        return symbol in self.table

    def getAddress(self, symbol: str) -> int:
        return self.table[symbol]

class Code:
    def __init__(self):
        # Table for destinations.
        self.d_table = {
            "": "000",
            "M": "001",
            "D": "010",
            "MD": "011",
            "A": "100",
            "AM": "101",
            "AD": "110",
            "AMD": "111"
        }

        # Table for comparisons.
        self.c_table = {
            "0": "0101010",
            "1": "0111111",
            "-1": "0111010",
            "D": "0001100",
            "A": "0110000",
            "M": "1110000",
            "!D": "0001101",
            "!A": "0110001",
            "!M": "1110001",
            "-D": "0001111",
            "-A": "0110011",
            "-M": "1110011",
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
            "D|M": "1010101"
        }

        # Table for jumps.
        self.j_table = {
            "": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111"
        }

    def dest(self, mnemonic: str) -> str:
        return self.d_table[mnemonic]

    def comp(self, mnemonic: str) -> str:
        return self.c_table[mnemonic]

    def jump(self, mnemonic: str) -> str:
        return self.j_table[mnemonic]


class Parser:

    def __init__(self, file_name: str):
        # Current command that's being processed.
        self.cmd = ""
        # Current command index.
        self.current = -1
        # All commands from the input file.
        self.commands = []
        # Open the file and prepare for parsing.
        # Remove all comments, empty lines, and whitespace characters.
        file = open(file_name)
        for line in file:
            line = line.partition("//")[0]
            line = line.strip()
            line = line.replace(" ", "")
            if line:
                self.commands.append(line)
        file.close()

    def hasMoreCommands(self) -> bool:
        return (self.current + 1) < len(self.commands)

    def advance(self) -> None:
        self.current += 1
        self.cmd = self.commands[self.current]

    def restart(self) -> None:
        self.cmd = ""
        self.current = -1

    def commandType(self) -> str:
        if self.cmd[0] == "@":
            return "A"
        elif self.cmd[0] == "(":
            return "L"
        else:
            return "C"

    def symbol(self) -> str:
        # @SCREEN, @256, (LABEL)
        if self.commandType() == "A":
            return self.cmd[1:]
        if self.commandType() == "L":
            return self.cmd[1:-1]
        return ""

    def dest(self) -> str:
        if self.commandType() == "C":
            if "=" in self.cmd:
                return self.cmd.partition("=")[0]
        return ""

    def comp(self) -> str:
        if self.commandType() == "C":
            tmp = self.cmd
            if "=" in tmp:
                tmp = tmp.partition("=")[2]
            return tmp.partition(";")[0]
        return ""

    def jump(self) -> str:
        if self.commandType() == "C":
            tmp = self.cmd
            if "=" in tmp:
                tmp = tmp.partition("=")[2]
            return tmp.partition(";")[2]
        return ""


def main():

    # Check if a file name is given.
    if len(sys.argv) != 2:
        print("Put file")
        print("using  " + os.path.basename(__file__) + " [file.asm]")
        return

    # Create a parser with the input file.
    input_file_name = sys.argv[1]
    parser = Parser(input_file_name)

    # Initiate the symbol table.
    symbols = SymbolTable()

    # Scan the input file for labels and add them to the symbol table.
    counter = 0
    while parser.hasMoreCommands():
        parser.advance()
        # If the command is a label, add it to the symbol table.
        # Otherwise increase the program line counter.
        if parser.commandType() == "L":
            symbols.addEntry(parser.symbol(), counter)
        else:
            counter += 1

    parser.restart()
    coder = Code()
    # Open the output file with the same name but .hack extension.
    output_file_name = input_file_name.replace(".asm", ".hack")
    file = open(output_file_name, "w")

    # User defined variables starts from memory position 16.
    variable = 16
    while parser.hasMoreCommands():
        parser.advance()
        # Check for the command type and convert the command into binary code.
        # A-Commands can be a constant, a symbol, or a variable declaration.
        if parser.commandType() == "A":
            num = 0
            symbol = parser.symbol()
            # Constant
            if symbol.isdecimal():
                num = int(symbol)
            elif symbols.contains(symbol):
                num = symbols.getAddress(symbol)
            else:
                num = variable
                symbols.addEntry(symbol, num)
                variable += 1
            file.write(format(num, "016b"))
            file.write("\n")
        # C-Commands are made out of a destination, a comparison, and a jump part.
        elif parser.commandType() == "C":
            # Obtain the binary coding from the coder and write it into the output file.
            comp = coder.comp(parser.comp())
            dest = coder.dest(parser.dest())
            jump = coder.jump(parser.jump())
            file.write("111" + comp + dest + jump)
            file.write("\n")
        else:
            pass
    file.close()

if __name__ == "__main__":
    main()
