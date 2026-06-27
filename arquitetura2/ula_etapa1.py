# ====================================
# TRABALHO DE ARQUITETURA 2
# PROFESSORA: SARAH PONTES
# GRUPO: LUÍS FELIPE FAHNING, GUILHERME DE SOUSA, CAIO FIGUEIREDO
import sys

NUM_BITS = 32

def int_para_bin32(n):
    
    return format(n & 0xFFFFFFFF, '032b')

def executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC):
    carry = INC   # carry-in entra no bit menos significativo
    resultado = 0

    # Percorre do bit 0 (LSB) até o bit 31 (MSB) — sentido correto do somador ripple-carry
    for bit in range(0, NUM_BITS):
        a_bit = (A >> bit) & 1
        b_bit = (B >> bit) & 1

        # Etapa 1: habilitação das entradas
        a = a_bit if ENA else 0
        b = b_bit if ENB else 0

        # Etapa 2: inversão de A (complemento bit a bit)
        if INVA:
            a = 1 - a

        # Etapa 3: unidade lógica — seleciona operação pelos bits F1, F0
        if F1 == 0 and F0 == 0:
            logico = a & b          # AND
        elif F1 == 0 and F0 == 1:
            logico = a | b          # OR
        elif F1 == 1 and F0 == 0:
            logico = 1 - b          # NOT B
        else:                        # F1=1, F0=1
            logico = a + b          # soma aritmética (entra no somador completo)

        # Etapa 4: somador completo com carry ripple
        total = logico + carry
        s_bit = total % 2           # bit de soma (XOR)
        carry = total // 2          # carry-out deste bit → carry-in do próximo

        resultado |= (s_bit << bit)

    return resultado, carry  # carry final = carry-out do bit 31

def executar_programa(arquivo_instrucoes, A_init, B_init, arquivo_log="saida_etapa1.txt"):
    with open(arquivo_instrucoes, 'r') as f_instrucoes, \
         open(arquivo_log, 'w') as f_log:

        instrucoes = [l.strip() for l in f_instrucoes if l.strip() and not l.startswith('#')]

        A = A_init & 0xFFFFFFFF
        B = B_init & 0xFFFFFFFF

        # Cabeçalho (estado inicial dos registradores)
        f_log.write(f"b = {int_para_bin32(B)}\n")
        f_log.write(f"a = {int_para_bin32(A)}\n\n")
        f_log.write("Start of Program\n")
        f_log.write("=" * 60 + "\n")

        PC = 1
        for IR in instrucoes:
            if len(IR) != 6 or not all(c in '01' for c in IR):
                print(f"[AVISO] Instrução inválida PC={PC}: '{IR}' — ignorada")
                PC += 1
                continue

            f_log.write(f"Cycle {PC}\n\n")
            f_log.write(f"PC = {PC}\n")

            # Decodificação — formato: F1 F0 ENA ENB INVA INC
            #                posição:   0   1   2   3    4   5
            F1   = int(IR[0])
            F0   = int(IR[1])
            ENA  = int(IR[2])
            ENB  = int(IR[3])
            INVA = int(IR[4])
            INC  = int(IR[5])

            S, co = executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC)

            f_log.write(f"IR = {IR}\n")
            f_log.write(f"b = {int_para_bin32(B)}\n")
            f_log.write(f"a = {int_para_bin32(A)}\n")
            f_log.write(f"s = {int_para_bin32(S)}\n")
            f_log.write(f"co = {co}\n")
            f_log.write("=" * 60 + "\n")

            PC += 1

        # Ciclo final — EOP
        f_log.write(f"Cycle {PC}\n\n")
        f_log.write(f"PC = {PC}\n")
        f_log.write("> Line is empty, EOP.\n")

    print(f"Execução concluída. Log salvo em '{arquivo_log}'")

def main():
    if len(sys.argv) < 2:
        print("Uso: python ula_etapa1.py <arquivo_instrucoes> [A] [B]")
        print()
        print("  arquivo_instrucoes : arquivo .txt com instruções de 6 bits")
        print("  A                  : valor inteiro de A em decimal (padrão: 0)")
        print("  B                  : valor inteiro de B em decimal (padrão: 0)")
        print()
        print("Exemplo: python ula_etapa1.py programa_etapa1.txt -1 1")
        sys.exit(1)

    arquivo_instrucoes = sys.argv[1]
    A = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    B = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    executar_programa(arquivo_instrucoes, A, B)

if __name__ == "__main__":
    main()