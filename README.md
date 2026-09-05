# Codificador Educativo de Instrucciones RISC-V

Herramienta que traduce una instrucción del subconjunto RV32I a su codificación
binaria de 32 bits y muestra el desglose de cada campo del formato
correspondiente (R, I, S o B).

CE-4301 Arquitectura de Computadores I. Proyecto Individual, 2026-II.

La documentación técnica completa está en [`docs/documentacion.md`](docs/documentacion.md).

---

## Preparación del entorno

La herramienta usa únicamente la biblioteca estándar de Python, así que no hay
dependencias que instalar.

**Requisito:** Python 3.10 o superior. La sintaxis `int | None` que usa el
código no existe en versiones anteriores. Se probó con Python 3.14.4.

En Ubuntu, Python ya viene instalado. Para verificar la versión:

```bash
python3 --version
```

Si hiciera falta instalarlo:

```bash
sudo apt update
sudo apt install python3
```

El script `run.sh` debe tener permiso de ejecución. Si al clonar el repositorio
se perdió ese permiso:

```bash
chmod +x run.sh
```

Con eso la herramienta ya está lista para usarse.

---

## Instrucciones soportadas

| Categoría                   | Formato | Instrucciones        |
|-----------------------------|---------|----------------------|
| Aritmética registro-registro| R       | `add`, `sub`, `and`, `or` |
| Aritmética con inmediato    | I       | `addi`, `andi`       |
| Carga desde memoria         | I       | `lw`, `lb`           |
| Almacenamiento en memoria   | S       | `sw`, `sb`           |
| Salto condicional           | B       | `beq`, `bne`         |

Los registros se escriben en notación `xN`, con N entre 0 y 31. Los nombres ABI
(`sp`, `a0`, `t0`) no están soportados. Los inmediatos y los offsets de salto se
reciben ya resueltos como valores numéricos: no se admiten etiquetas.

---

## Estructura del repositorio

```
run.sh                     punto de entrada
encoder.py                 codificador y generador del desglose
vectores_ejemplo.txt       vectores de autoverificación (del kit)
docs/documentacion.md      documentación técnica
validacion/casos.txt       36 casos de prueba propios
validacion/validar.sh      script de comparación contra el toolchain
validacion/resultados.txt  evidencia de la validación
```

---

## Validación contra el toolchain oficial

Esta sección solo hace falta para reproducir la validación documentada. **No es
necesaria para ejecutar la herramienta.**

### Instalación del toolchain

En Ubuntu, el paquete de binutils para RISC-V trae el ensamblador y `objdump`,
que es todo lo que se necesita. No hace falta compilar el toolchain completo
desde fuente ni instalar GCC:

```bash
sudo apt update
sudo apt install binutils-riscv64-unknown-elf
```

Verificar:

```bash
riscv64-unknown-elf-as --version
riscv64-unknown-elf-objdump --version
```

El binario se llama `riscv64` pero produce código de 32 bits al pasarle
`-march=rv32i -mabi=ilp32`. El propio `objdump` lo confirma en su salida, donde
reporta el formato `elf32-littleriscv`.

### Uso manual del toolchain

Para obtener la codificación de referencia de una instrucción:

```bash
echo "addi x10, x1, -12" > /tmp/t.s
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o /tmp/t.o /tmp/t.s
riscv64-unknown-elf-objdump -d /tmp/t.o
```

En la salida, la segunda columna es la codificación en hexadecimal. Los
registros aparecen con nombres ABI (`a0` en lugar de `x10`), pero eso solo
afecta la representación textual, no el hex.

**Los saltos condicionales requieren una sintaxis distinta.** GNU `as`
interpreta un número pelado en un branch como dirección absoluta, no como
desplazamiento relativo, y aplica *branch relaxation*: reemplaza la instrucción
por un branch invertido seguido de un salto incondicional. Para evitarlo hay que
escribir el offset respecto de `.`, que denota la posición actual:

```bash
printf 'beq x1, x2, .+8\n' > /tmp/t.s
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o /tmp/t.o /tmp/t.s
riscv64-unknown-elf-objdump -d /tmp/t.o
```

Con offset negativo, `.-80`. Esto aplica solo a `beq` y `bne`; en las demás
instrucciones el número no es una dirección y se pasa tal cual.

El detalle completo está en la sección 3.3 de la documentación técnica.

### Ejecutar la validación

```bash
./validacion/validar.sh
```

El script recorre `validacion/casos.txt`, ensambla cada caso con el toolchain,
y compara la codificación de referencia contra la salida de la herramienta.

Para regenerar la evidencia:

```bash
./validacion/validar.sh > validacion/resultados.txt
```