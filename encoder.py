#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import sys
from dataclasses import dataclass

SOPORTADAS = ["add", "sub", "and", "or", "addi", "andi",
              "lw", "lb", "sw", "sb", "beq", "bne"]

#Definicio de clase para representar el formato de la instruccion
@dataclass(frozen=True)
class InstrDef:
    formato: str
    forma: str
    opcode: int
    funct3: int
    funct7: int | None = None

#Fuente: RISC-V ISA Manual Vol. I (Cap. 24) y Harris, Apéndice B, Tabla B.1
#Diccionario que contiene para cada instruccion su tipo, los atributos esperados, y los valores en binario de opcode, fucnt3 y funct7 para donde aplique
DIRINSTR: dict[str, InstrDef] = {
    "add":  InstrDef("R", "rd, rs1, rs2",  0b0110011, 0b000, 0b0000000),
    "sub":  InstrDef("R", "rd, rs1, rs2",  0b0110011, 0b000, 0b0100000),
    "or":   InstrDef("R", "rd, rs1, rs2",  0b0110011, 0b110, 0b0000000),
    "and":  InstrDef("R", "rd, rs1, rs2",  0b0110011, 0b111, 0b0000000),
    "addi": InstrDef("I", "rd, rs1, imm",  0b0010011, 0b000),
    "andi": InstrDef("I", "rd, rs1, imm",  0b0010011, 0b111),
    "lb":   InstrDef("I", "rd, imm(rs1)",  0b0000011, 0b000),
    "lw":   InstrDef("I", "rd, imm(rs1)",  0b0000011, 0b010),
    "sb":   InstrDef("S", "rs2, imm(rs1)", 0b0100011, 0b000),
    "sw":   InstrDef("S", "rs2, imm(rs1)", 0b0100011, 0b010),
    "beq":  InstrDef("B", "rs1, rs2, imm", 0b1100011, 0b000),
    "bne":  InstrDef("B", "rs1, rs2, imm", 0b1100011, 0b001),
}

#Definicio de clase representar un elemento de la instruccion en binario
@dataclass(frozen=True)
class Campo:
    nombre: str
    posInstr: int
    ancho: int
    bitOrigen: int = 0
    desc: str = ""

LAYOUTS: dict[str, list[Campo]] = {
    "R": [
        Campo("funct7", 25, 7, 0, "Distingue operaciones con igual opcode y funct3"),
        Campo("rs2",    20, 5, 0, "Segundo registro fuente"),
        Campo("rs1",    15, 5, 0, "Primer registro fuente"),
        Campo("funct3", 12, 3, 0, "Selecciona la operacion dentro del opcode"),
        Campo("rd",      7, 5, 0, "Registro destino"),
        Campo("opcode",  0, 7, 0, "Clase de instruccion: aritmetica registro-registro"),
    ],
    "I": [
        Campo("imm[11:0]", 20, 12, 0, "Inmediato de 12 bits con signo"),
        Campo("rs1",       15,  5, 0, "Registro fuente / base de la direccion"),
        Campo("funct3",    12,  3, 0, "Selecciona la operacion dentro del opcode"),
        Campo("rd",         7,  5, 0, "Registro destino"),
        Campo("opcode",     0,  7, 0, "Clase de instruccion: inmediato o carga"),
    ],
    "S": [
        Campo("imm[11:5]", 25, 7, 5, "Parte alta del offset de 12 bits"),
        Campo("rs2",       20, 5, 0, "Registro con el dato a almacenar"),
        Campo("rs1",       15, 5, 0, "Registro base de la direccion"),
        Campo("funct3",    12, 3, 0, "Selecciona el ancho del almacenamiento"),
        Campo("imm[4:0]",   7, 5, 0, "Parte baja del offset de 12 bits"),
        Campo("opcode",     0, 7, 0, "Clase de instruccion: almacenamiento"),
    ],
    "B": [
        Campo("imm[12]",   31, 1, 12, "Bit de signo del offset"),
        Campo("imm[10:5]", 25, 6,  5, "Bits 10 a 5 del offset"),
        Campo("rs2",       20, 5,  0, "Segundo registro a comparar"),
        Campo("rs1",       15, 5,  0, "Primer registro a comparar"),
        Campo("funct3",    12, 3,  0, "Selecciona la condicion de salto"),
        Campo("imm[4:1]",   8, 4,  1, "Bits 4 a 1 del offset"),
        Campo("imm[11]",    7, 1, 11, "Bit 11 del offset (reubicado)"),
        Campo("opcode",     0, 7,  0, "Clase de instruccion: salto condicional"),
    ],
}

def parse_register(reg: str) -> int:
    """
    Recibe un registro como texto, p. ej. "x5", y retorna su número como
    entero (0 <= valor < 32). Debe validar que el registro sea válido.
    """
    if not reg.startswith("x"):
        raise ValueError(f"Registro inválido: {reg}")
    try:
        reg_num = int(reg[1:])
    except ValueError:
        raise ValueError(f"Registro inválido: {reg}")
    if not (0 <= reg_num < 32):
        raise ValueError(f"Registro fuera de rango: {reg}")
    return reg_num

def parse_immediate(imm: str) -> int:
    """
    Recibe un inmediato como texto, p. ej. "42" o "-1", y retorna su valor
    como entero (puede ser negativo). Debe validar que el inmediato sea
    un número entero válido.
    """
    try:
        return int(imm)
    except ValueError:
        raise ValueError(f"Inmediato inválido: {imm}")

def parse_offset(offset: str) -> tuple[int, int]:
    """
    Recibe un offset como texto, p. ej. "8(x5)", y retorna una tupla con
    el inmediato y el registro base como enteros (inmediato, registro).
    Debe validar que el offset sea válido.
    """
    if "(" not in offset or not offset.endswith(")"):
        raise ValueError(f"Offset inválido: {offset}")
    imm_str, reg_str = offset.split("(")
    reg_str = reg_str[:-1]  # Remove the closing parenthesis
    imm = parse_immediate(imm_str)
    reg = parse_register(reg_str)
    return imm, reg

def encode_r_instruction(instr: InstrDef, operands: str) -> int:
    listOperands = operands.split(",")
    if len(listOperands) != 3:
        raise ValueError(f"R-type instruction requires 3 operands, got {len(listOperands)}")
    rd = parse_register(listOperands[0].strip())
    rs1 = parse_register(listOperands[1].strip())
    rs2 = parse_register(listOperands[2].strip())
    opcode = instr.opcode
    funct3 = instr.funct3
    funct7 = instr.funct7 if instr.funct7 is not None else 0
    layout = LAYOUTS["R"]
    word = (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
    return word

def encode_i_instruction(instr: InstrDef, operands: str) -> int:
    listOperands = operands.split(",")
    if len(listOperands) == 3:
        rd = parse_register(listOperands[0].strip())
        rs1 = parse_register(listOperands[1].strip())
        imm = parse_immediate(listOperands[2].strip())
        opcode = instr.opcode
        funct3 = instr.funct3
        imm12 = imm & 0xFFF
        word = (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
        return word
    if len(listOperands) == 2:
        rd = parse_register(listOperands[0].strip())
        imm, rs1 = parse_offset(listOperands[1].strip())
        opcode = instr.opcode
        funct3 = instr.funct3
        imm12 = imm & 0xFFF
        word = (imm12 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode
        return word
    raise ValueError(f"I-type instruction requires 2 or 3 operands, got {len(listOperands)}")

def encode_s_instruction(instr: InstrDef, operands: str) -> int:
    listOperands = operands.split(",")
    if len(listOperands) != 2:
        raise ValueError(f"S-type instruction requires 2 operands, got {len(listOperands)}")
    rs2 = parse_register(listOperands[0].strip())
    imm, rs1 = parse_offset(listOperands[1].strip())
    opcode = instr.opcode
    funct3 = instr.funct3
    imm11_5 = (imm >> 5) & 0x7F
    imm4_0 = imm & 0x1F
    word = (imm11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_0 << 7) | opcode
    return word

def encode_b_instruction(instr: InstrDef, operands: str) -> int:
    listOperands = operands.split(",")
    if len(listOperands) != 3:
        raise ValueError(f"B-type instruction requires 3 operands, got {len(listOperands)}")
    rs1 = parse_register(listOperands[0].strip())
    rs2 = parse_register(listOperands[1].strip())
    imm = parse_immediate(listOperands[2].strip())
    opcode = instr.opcode
    funct3 = instr.funct3
    imm12 = (imm >> 12) & 0x1
    imm10_5 = (imm >> 5) & 0x3F
    imm4_1 = (imm >> 1) & 0xF
    imm11 = (imm >> 11) & 0x1
    word = (imm12 << 31) | (imm10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | opcode
    return word

def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe
    retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """

    instruction = instruction.strip()
    #Valida si el string de instruccion esta vacio
    if not instruction:
        raise ValueError("La instrucción no puede estar vacía")

    #Separa el mnemónico de los operandos
    instr=instruction.split(" ",1)

    #valida si el mnemónico de la instrucción es soportado
    instrHead = instr[0].strip()
    if instrHead not in DIRINSTR:
        raise ValueError(f"Instrucción no soportada: {instrHead}. Soportadas: {', '.join(DIRINSTR)}")

    #Valida si hay operandos para la instrucción
    if len(instr) < 2:
            raise ValueError(f"Faltan operandos para: {instrHead}")
    instrBody = instr[1].strip()
    instrDir = DIRINSTR[instrHead]

    if instrDir.formato == "R":
        return encode_r_instruction(instrDir, instrBody)
    elif instrDir.formato == "I":
        return encode_i_instruction(instrDir, instrBody)
    elif instrDir.formato == "S":
        return encode_s_instruction(instrDir, instrBody)
    elif instrDir.formato == "B":
        return encode_b_instruction(instrDir, instrBody)
    else:
        raise ValueError(f"Formato desconocido para la instrucción: {instrHead}")



def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    instruccion = instruction.strip()
    mnemonico = instruccion.split(" ", 1)[0]
    formato = DIRINSTR[mnemonico].formato

    output = [f"Formato: {formato}",""]
    output.append(f"{'Campo':<10} {'Bits':<7} {'Binario':<13} {'Dec':>6} Significado")
    output.append("-" * 90)

    partes = []
    for campo in LAYOUTS[formato]:
        valor = (word >> campo.posInstr) & ((1 << campo.ancho) - 1)
        binario = f"{valor:0{campo.ancho}b}"
        partes.append(binario)

        decimal = valor #para el imm de operaciones I
        if formato == "I" and campo.nombre.startswith("imm"):
            if valor & (1 << (campo.ancho - 1)):
                decimal -= (1 << campo.ancho)
        alto = campo.posInstr + campo.ancho - 1
        rango = f"{alto}-{campo.posInstr}" if campo.ancho > 1 else f"{alto}"
        output.append(f"{campo.nombre:<10} {rango:<7} {binario:<13} {decimal:>6}  {campo.desc}")

    if formato in ("S", "B"):
        bits = 13 if formato == "B" else 12
        imm_total = 0
        for campo in LAYOUTS[formato]:
            if campo.nombre.startswith("imm"):
                valor = (word >> campo.posInstr) & ((1 << campo.ancho) - 1)
                imm_total |= (valor << campo.bitOrigen)
        if imm_total & (1 << (bits - 1)):
            imm_total -= (1 << bits)
        binario_imm = f"{imm_total & ((1 << bits) - 1):0{bits}b}"
        output.append(f"{'imm total':<10} {'-':<7} {binario_imm:<13} {imm_total:>6}  Inmediato completo con signo")

    output.append("")
    output.append(" ".join(partes))

    return "\n".join(output)


def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
