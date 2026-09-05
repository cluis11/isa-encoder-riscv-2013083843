# Documentación técnica

**Codificador Educativo de Instrucciones RISC-V (subconjunto RV32I)**
CE-4301 Arquitectura de Computadores I. Proyecto Individual, 2026-II

---

## 1. Arquitectura del código y decisiones de diseño

### 1.1 Estructura general

La herramienta está en un solo archivo, `encoder.py`, que se invoca desde
`run.sh`. La idea central del diseño es separar el dato (la especificación de la
ISA) del algoritmo (el parseo del texto y el armado de los bits). Todo lo que
cambia de una instrucción a otra vive en dos tablas, y ninguna posición de bit
está escrita dentro de la lógica.

`DIRINSTR` mapea cada mnemónico a un `InstrDef`, que guarda su formato, la
sintaxis de sus operandos y los valores fijos de `opcode`, `funct3` y `funct7`.

`LAYOUTS` mapea cada formato a la lista de `Campo` que lo compone: qué campos
tiene, en qué bits de la palabra va cada uno, de qué bit del valor de origen se
toma, y una descripción de su rol.

El flujo de una codificación es:

```
texto -> encode_instruction()      valida y despacha por formato
      -> encode_X_instruction()    parsea operandos y arma la palabra
      -> entero de 32 bits
```

`explain_instruction()` recorre el camino inverso: extrae cada campo desde la
palabra ya codificada, leyendo la misma tabla `LAYOUTS`.

### 1.2 Decisiones de diseño

**Tablas de datos en lugar de lógica por instrucción.** La tabla tiene 12
entradas y con ellas se codifica cualquier combinación de registros e
inmediatos. Agregar una instrucción de un formato ya soportado es agregar una
fila, sin escribir lógica nueva. Es el mismo patrón que usan los ensambladores
reales, donde un motor genérico interpreta tablas que describen las
instrucciones.

**`formato` y `forma` son campos separados.** El formato (R, I, S, B) determina
el layout de bits; la forma determina cómo se parsea el texto. Hacen falta los
dos porque el formato I admite dos sintaxis distintas, `addi rd, rs1, imm` y
`lw rd, imm(rs1)`, sobre un mismo layout. De ahí que haya 4 formatos y 5 formas.

**La llave de la tabla es el mnemónico.** Ni el formato ni el opcode alcanzan
por sí solos. `addi` y `lw` comparten formato pero tienen opcodes distintos, y
`add` y `sub` comparten opcode y `funct3`, diferenciándose solo en `funct7`.

**`funct7` vale `None` donde no aplica.** En los formatos I, S y B ese campo no
existe. Usar `None` en lugar de `0` es más honesto, y hace que un uso indebido
falle en vez de codificar un cero espurio.

**Los opcodes se escriben en binario con su ancho completo.** Así se pueden
comparar de un vistazo contra las tablas del manual, sin conversión mental.

**Las posiciones de bits están declaradas en un solo lugar.** La posición de
cada campo se necesita dos veces: para armar la palabra y para dibujar el
desglose. Al vivir únicamente en `LAYOUTS`, las dos representaciones no pueden
desincronizarse.

**Se trabaja con operaciones de bits, no con cadenas de texto.** Los valores se
manejan como enteros y se colocan con corrimientos que después se combinan con
OR. Como cada campo ocupa un rango disjunto, los valores se acomodan sin
pisarse. La alternativa, concatenar cadenas binarias, obligaría a manejar el
relleno y el complemento a dos a mano, y complicaría bastante el armado de S y
B.

**El enmascarado del inmediato.** En Python los enteros no tienen ancho fijo, de
modo que un valor negativo arrastra unos hacia la izquierda indefinidamente y
contaminaría los demás campos al hacer OR. Enmascarar al ancho del campo
(`imm & 0xFFF`) resuelve eso, y es además exactamente el paso de conversión a
complemento a dos.

**El campo `bitOrigen`.** Indica desde qué bit del valor de origen se toma el
contenido de cada campo. Vale 0 para registros y campos fijos, pero es distinto
de cero en los trozos de inmediato de S y B. Gracias a él hay una sola fórmula
de extracción para todos los campos:

```
(origen >> bitOrigen) & ((1 << ancho) - 1)
```

**El bit 0 del formato B se descarta sin código especial.** Los destinos de
salto están alineados a 2 bytes, así que el bit 0 del offset siempre vale cero y
no se codifica. Como ningún campo de B declara `bitOrigen = 0`, ese bit nunca se
lee. El descarte sale del propio recorrido de la tabla, no de un paso aparte.

**La fila de inmediato completo en el desglose.** En S y B el inmediato aparece
partido en varios trozos, y su valor real no se ve en ninguna fila individual:
en un `beq`, leer `imm[10:5]=61` e `imm[4:1]=8` no dice que el salto era de -80
bytes. Por eso se agrega una fila final que rearma los trozos usando `bitOrigen`
y aplica la extensión de signo.

**El separador de operandos es la coma.** El espacio solo es obligatorio después
del mnemónico. La entrada se parte primero por ese espacio y luego por comas,
limpiando cada token, lo que hace equivalentes `add x7, x20, x6`,
`add x7,x20,x6` y `add   x7 ,x20,  x6`.

**No hay dependencias externas.** Solo se usan `sys` y `dataclasses`, ambos de
la biblioteca estándar. Eso reduce la preparación del entorno a tener Python
3.10 o superior, que es lo que pide la sintaxis `int | None`.

### 1.3 Instrucciones soportadas

| Instrucción | Formato | Sintaxis        | opcode  | funct3 | funct7    |
|-------------|---------|-----------------|---------|--------|-----------|
| `add`       | R       | `rd, rs1, rs2`  | 0110011 | 000    | 0000000   |
| `sub`       | R       | `rd, rs1, rs2`  | 0110011 | 000    | 0100000   |
| `or`        | R       | `rd, rs1, rs2`  | 0110011 | 110    | 0000000   |
| `and`       | R       | `rd, rs1, rs2`  | 0110011 | 111    | 0000000   |
| `addi`      | I       | `rd, rs1, imm`  | 0010011 | 000    | no aplica |
| `andi`      | I       | `rd, rs1, imm`  | 0010011 | 111    | no aplica |
| `lb`        | I       | `rd, imm(rs1)`  | 0000011 | 000    | no aplica |
| `lw`        | I       | `rd, imm(rs1)`  | 0000011 | 010    | no aplica |
| `sb`        | S       | `rs2, imm(rs1)` | 0100011 | 000    | no aplica |
| `sw`        | S       | `rs2, imm(rs1)` | 0100011 | 010    | no aplica |
| `beq`       | B       | `rs1, rs2, imm` | 1100011 | 000    | no aplica |
| `bne`       | B       | `rs1, rs2, imm` | 1100011 | 001    | no aplica |

Vale la pena notar que el opcode agrupa por clase de operación, no por formato.
`addi` y `lw` son ambos formato I pero tienen opcodes distintos, porque uno es
aritmética con inmediato y el otro una carga desde memoria.

### 1.4 Layout de bits por formato

```
R:  funct7[31:25]  rs2[24:20]  rs1[19:15]  funct3[14:12]  rd[11:7]  opcode[6:0]

I:  imm[11:0] -> 31:20         rs1[19:15]  funct3[14:12]  rd[11:7]  opcode[6:0]

S:  imm[11:5] -> 31:25   rs2[24:20]  rs1[19:15]  funct3[14:12]
    imm[4:0]  -> 11:7    opcode[6:0]

B:  imm[12]   -> 31      imm[10:5] -> 30:25   rs2[24:20]  rs1[19:15]
    funct3[14:12]        imm[4:1]  -> 11:8    imm[11] -> 7   opcode[6:0]
```

Cada layout cubre exactamente los 32 bits, sin huecos ni solapes.

---

## 2. Ejemplos de salida explicativa

Uno por cada formato soportado.

### 2.1 Formato R

```
$ ./run.sh "sub x7, x20, x6"
Formato: R

Campo      Bits    Binario          Dec Significado
------------------------------------------------------------------------------------------
funct7     31-25   0100000           32  Distingue operaciones con igual opcode y funct3
rs2        24-20   00110              6  Segundo registro fuente
rs1        19-15   10100             20  Primer registro fuente
funct3     14-12   000                0  Selecciona la operacion dentro del opcode
rd         11-7    00111              7  Registro destino
opcode     6-0     0110011           51  Clase de instruccion: aritmetica registro-registro

0100000 00110 10100 000 00111 0110011
HEX: 0x406a03b3
```

Se elige `sub` en vez de `add` porque deja ver el rol de `funct7`: vale
`0100000` en lugar de `0000000`, y esa es la única diferencia entre las dos
instrucciones, que comparten `opcode` y `funct3`.

### 2.2 Formato I

```
$ ./run.sh "addi x10, x1, -12"
Formato: I

Campo      Bits    Binario          Dec Significado
------------------------------------------------------------------------------------------
imm[11:0]  31-20   111111110100     -12  Inmediato de 12 bits con signo
rs1        19-15   00001              1  Registro fuente / base de la direccion
funct3     14-12   000                0  Selecciona la operacion dentro del opcode
rd         11-7    01010             10  Registro destino
opcode     6-0     0010011           19  Clase de instruccion: inmediato o carga

111111110100 00001 000 01010 0010011
HEX: 0xff408513
```

El inmediato ocupa un único campo contiguo en los bits 31:20. Su binario,
`111111110100`, es la representación en complemento a dos de -12 en 12 bits, y
por eso la columna decimal lo muestra ya interpretado con signo.

### 2.3 Formato S

```
$ ./run.sh "sw x8, -4(x2)"
Formato: S

Campo      Bits    Binario          Dec Significado
------------------------------------------------------------------------------------------
imm[11:5]  31-25   1111111          127  Parte alta del offset de 12 bits
rs2        24-20   01000              8  Registro con el dato a almacenar
rs1        19-15   00010              2  Registro base de la direccion
funct3     14-12   010                2  Selecciona el ancho del almacenamiento
imm[4:0]   11-7    11100             28  Parte baja del offset de 12 bits
opcode     6-0     0100011           35  Clase de instruccion: almacenamiento
imm total  -       111111111100      -4  Inmediato completo con signo

1111111 01000 00010 010 11100 0100011
HEX: 0xfe812e23
```

Acá el inmediato viene partido en dos trozos: `imm[11:5]` vale 127 e `imm[4:0]`
vale 28. Por separado no significan nada, y de ahí la utilidad de la fila
`imm total`, que los rearma y muestra el offset real, -4.

Otro detalle visible es que el registro de la izquierda, `x8`, es `rs2` y no un
destino: es el registro cuyo dato se escribe en memoria.

### 2.4 Formato B

```
$ ./run.sh "beq x1, x2, -80"
Formato: B

Campo      Bits    Binario          Dec Significado
------------------------------------------------------------------------------------------
imm[12]    31      1                  1  Bit de signo del offset
imm[10:5]  30-25   111101            61  Bits 10 a 5 del offset
rs2        24-20   00010              2  Segundo registro a comparar
rs1        19-15   00001              1  Primer registro a comparar
funct3     14-12   000                0  Selecciona la condicion de salto
imm[4:1]   11-8    1000               8  Bits 4 a 1 del offset
imm[11]    7       1                  1  Bit 11 del offset (reubicado)
opcode     6-0     1100011           99  Clase de instruccion: salto condicional
imm total  -       1111110110000    -80  Inmediato completo con signo

1 111101 00010 00001 000 1000 1 1100011
HEX: 0xfa2088e3
```

Este es el caso más ilustrativo de los cuatro. El offset se reparte en cuatro
trozos no contiguos y reordenados: `imm[12]` va al bit 31 mientras que `imm[11]`
va al bit 7, muy por debajo. Ese reordenamiento, que Harris llama *bit
swizzling*, mantiene el bit de signo siempre en el bit 31 y alinea el resto de
los bits del inmediato con las posiciones que ocupan en el formato S, lo que
simplifica el hardware de decodificación.

El bit 0 del offset no aparece en ningún campo. Como los destinos de salto están
alineados a 2 bytes, siempre vale cero y se omite de la codificación.

---

## 3. Validación contra el toolchain oficial

### 3.1 Metodología

Se construyeron 36 casos de prueba, 12 instrucciones por 3 escenarios cada una:
valor positivo, valor negativo y valor límite. Están listados en
`validacion/casos.txt`.

Para las instrucciones de formato R, que no llevan inmediato, los tres
escenarios se cubrieron variando los registros: valores normales, uso de `x0`, y
el extremo del rango con `x31`.

Cada caso se ensambla con el toolchain oficial rv32, se obtiene su codificación
de referencia con `objdump -d`, y se compara contra la salida de la herramienta
propia.

### 3.2 Ejecución

```bash
./validacion/validar.sh
```

Para guardar la evidencia:

```bash
./validacion/validar.sh > validacion/resultados.txt
```

El script recorre `validacion/casos.txt` y para cada instrucción imprime una
fila con la instrucción, el hex del modelo propio, el hex de referencia de
`objdump`, y si coinciden o no. Al final reporta el total.

### 3.3 Tratamiento especial de los saltos condicionales

Durante la validación apareció un problema con los `beq` y `bne`: en el
desensamblado la instrucción salía con la condición invertida y acompañada de un
salto incondicional que no estaba en el fuente, y el hex de referencia era
idéntico para offsets distintos, lo cual era claramente imposible.

La causa es que GNU `as` interpreta un número pelado en un branch como una
dirección absoluta, no como un desplazamiento relativo. Con `beq x1, x2, 8` el
ensamblador entiende "saltar a la dirección 8"; como esa dirección queda fuera
de la sección, no puede resolverla y emite la forma segura equivalente, que es
un branch con la condición invertida saltando por encima de un `j`. Ese
mecanismo se conoce como *branch relaxation*.

Conviene aclarar que esto no se desactiva con `-mno-relax`. Esa opción controla
la relajación del enlazador, que trabaja sobre secuencias `auipc`+`jalr` y sobre
el puntero global, y es un mecanismo distinto.

La solución que se adoptó fue reescribir el operando usando `.`, que en la
sintaxis de GNU `as` denota la posición actual. Así la expresión se resuelve
localmente y no queda nada por relajar:

```bash
# Falla: el ensamblador aplica branch relaxation
printf 'beq x1, x2, 8\n' > /tmp/t.s

# Correcto: el offset se resuelve respecto de la posición actual
printf 'beq x1, x2, .+8\n' > /tmp/t.s
```

El script aplica esta reescritura solo a `beq` y `bne`. Las demás instrucciones
se pasan tal cual, porque en ellas el número es un valor aritmético o un
desplazamiento respecto de un registro base, no una dirección.

El archivo `validacion/casos.txt` conserva la sintaxis con offset numérico, que
es la que recibe la herramienta propia. La reescritura con `.` es un artificio
interno del script, necesario solo para la herramienta de referencia.

### 3.4 Resultados

La evidencia completa de los 36 casos está en `validacion/resultados.txt`,
generado por el script. Los 36 coinciden con la codificación de referencia del
toolchain oficial.

### 3.5 Autoverificación adicional

Aparte de los 36 casos propios, la herramienta se contrastó también contra el
archivo `vectores_ejemplo.txt` que viene en el kit del proyecto, que trae
instrucciones con su codificación correcta. Los 36 vectores del kit también
coinciden.

---

## 4. Fuentes consultadas

Los valores de `opcode`, `funct3` y `funct7` de cada instrucción, y las
posiciones de bits de cada formato, se obtuvieron de las fuentes que siguen. En
la práctica los valores se leyeron de la Tabla B.1 de Harris, que es más cómoda
de consultar, y se verificaron de forma cruzada contra el manual oficial, que se
cita como fuente normativa.

**[1]** A. Waterman y K. Asanović. *The RISC-V Instruction Set Manual, Volume I:
User-Level ISA*, Document Version 20191213. RISC-V Foundation, 2019.

- Capítulo 2, sección 2.2: formatos base R, I, S y B, con la posición de cada
  campo (Figura 2.2).
- Capítulo 2, sección 2.3: variantes de inmediato y su reparto por formato
  (Figuras 2.3 y 2.4). Es la referencia normativa para el reordenamiento de bits
  del formato B.
- Capítulo 2, secciones 2.4 a 2.6: semántica de las instrucciones aritméticas,
  de salto condicional y de acceso a memoria.
- Capítulo 24: tablas de listado de opcodes de RV32I.

**[2]** S. Harris y D. Harris. *Digital Design and Computer Architecture, RISC-V
Edition*. Morgan Kaufmann, 2022.

- Apéndice B, Tabla B.1: listado de instrucciones RV32I con sus columnas de
  `op`, `funct3`, `funct7`, tipo y sintaxis.
- Apéndice B, Figura B.1: diagramas de los formatos con sus rangos de bits.
- Sección 6.4: formatos de instrucción, con ejemplos resueltos paso a paso. La
  sección 6.4.3 trata S y B en conjunto y explica el reordenamiento del
  inmediato de B.