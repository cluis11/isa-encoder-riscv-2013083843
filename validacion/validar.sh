#!/bin/bash
# Compara la salida de ./run.sh contra el toolchain oficial rv32.

cd "$(dirname "$0")/.." || exit 1

TMP=$(mktemp -d)
ok=0
fail=0

printf "%-26s %-12s %-12s %s\n" "INSTRUCCION" "MODELO" "OBJDUMP" "RESULTADO"
printf -- "-%.0s" {1..70}; echo

while read -r instr; do
    [[ -z "$instr" || "$instr" == \#* ]] && continue

    mnem=$(echo "$instr" | awk '{print $1}')

    if [[ "$mnem" == "beq" || "$mnem" == "bne" ]]; then
        # Los branches se reescriben usando una etiqueta con desplazamiento
        # para evitar que GNU as aplique branch relaxation.
        off=$(echo "$instr" | awk -F',' '{gsub(/ /,"",$3); print $3}')
        base=$(echo "$instr" | sed "s/,[^,]*$//")
        printf '.text\ninicio:\n    %s, inicio+%s\n' "$base" "$off" > "$TMP/t.s"
    else
        echo "$instr" > "$TMP/t.s"
    fi

    riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o "$TMP/t.o" "$TMP/t.s" 2>/dev/null
    ref=$(riscv64-unknown-elf-objdump -d "$TMP/t.o" | awk '/^ +0:/ {print $2}')
    ref="0x$ref"

    mio=$(./run.sh "$instr" 2>/dev/null | grep -oP 'HEX: \K0x[0-9a-fA-F]+')

    if [ "$mio" == "$ref" ]; then
        res="OK"; ok=$((ok+1))
    else
        res="FALLO"; fail=$((fail+1))
    fi
    printf "%-26s %-12s %-12s %s\n" "$instr" "$mio" "$ref" "$res"
done < validacion/casos.txt

rm -rf "$TMP"
echo
echo "Total: $ok correctos, $fail fallidos"