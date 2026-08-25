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

LAYOUTS: dict[str, list[Campo]] = {
    "R": [
        Campo("funct7", 25, 7),
        Campo("rs2", 20, 5),
        Campo("rs1", 15, 5),
        Campo("funct3", 12, 3),
        Campo("rd", 7, 5),
        Campo("opcode", 0, 7)
    ],
    "I": [
        Campo("imm[11:0]", 20, 12, 0),
        Campo("rs1", 15, 5),
        Campo("funct3", 12, 3),
        Campo("rd", 7, 5),
        Campo("opcode", 0, 7)    
    ],
    "S": [
        Campo("imm[11:5]", 25, 7, 5),
        Campo("rs2", 20, 5),
        Campo("rs1", 15, 5),
        Campo("funct3", 12, 3),
        Campo("imm[4:0]", 7, 5, 0),
        Campo("opcode", 0, 7)
    ],
    "B": [
        Campo("imm[12]", 31, 1, 12),
        Campo("imm[10:5]", 25, 6, 5),
        Campo("rs2", 20, 5),
        Campo("rs1", 15, 5),
        Campo("funct3", 12, 3),
        Campo("imm[4:1]", 8, 4, 1),
        Campo("imm[11]", 7, 1, 11),
        Campo("opcode", 0, 7)
    ]
}

def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe
    retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """
    # TODO: implementar. Sugerencia: parsear el mnemónico y los operandos,
    # despachar según el formato (R/I/S/B), y ensamblar los campos con
    # operaciones de bits.
    raise NotImplementedError("encode_instruction: pendiente de implementar")


def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    # TODO: implementar.
    raise NotImplementedError("explain_instruction: pendiente de implementar")


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
