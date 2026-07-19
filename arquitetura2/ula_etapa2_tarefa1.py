# ====================================
# TRABALHO DE ARQUITETURA 2
# PROFESSORA: SARAH PONTES
# GRUPO: LUÍS FELIPE FAHNING, GUILHERME DE SOUSA, CAIO FIGUEIREDO
# ETAPA 2 - TAREFA 1: ULA de 8 bits de controle, com deslocador (SLL8/SRA1) e saídas N e Z
import sys

from ula_etapa1 import executar_ula, int_para_bin32

NUM_BITS = 32
MASCARA = 0xFFFFFFFF


def deslocar(S, SLL8, SRA1):
    if SLL8:
        # desloca a saída S em 8 bits para a esquerda (lógico)
        return (S << 8) & MASCARA
    if SRA1:
        # desloca a saída S em 1 bit para a direita, preservando o bit de sinal (aritmético)
        assinado = S - (1 << NUM_BITS) if S & (1 << (NUM_BITS - 1)) else S
        return (assinado >> 1) & MASCARA
    return S


def flags_nz(valor):
    assinado = valor - (1 << NUM_BITS) if valor & (1 << (NUM_BITS - 1)) else valor
    N = 1 if assinado < 0 else 0
    Z = 1 if valor == 0 else 0
    return N, Z


def executar_programa(arquivo_instrucoes, A_init, B_init, arquivo_log="saida_etapa2_tarefa1.txt"):
    with open(arquivo_instrucoes, 'r') as f_instrucoes, \
         open(arquivo_log, 'w') as f_log:

        instrucoes = [l.strip() for l in f_instrucoes if l.strip() and not l.startswith('#')]

        A = A_init & MASCARA
        B = B_init & MASCARA

        # Cabeçalho (estado inicial dos registradores)
        f_log.write(f"b = {int_para_bin32(B)}\n")
        f_log.write(f"a = {int_para_bin32(A)}\n\n")
        f_log.write("Start of Program\n")
        f_log.write("=" * 60 + "\n")

        PC = 1
        for IR in instrucoes:
            if len(IR) != 8 or not all(c in '01' for c in IR):
                print(f"[AVISO] Instrução inválida PC={PC}: '{IR}' — ignorada")
                PC += 1
                continue

            f_log.write(f"Cycle {PC}\n\n")
            f_log.write(f"PC = {PC}\n")
            f_log.write(f"IR = {IR}\n")

            # Decodificação — formato: SLL8 SRA1 F1 F0 ENA ENB INVA INC
            #                posição:     0    1   2  3   4   5    6   7
            SLL8 = int(IR[0])
            SRA1 = int(IR[1])
            F1   = int(IR[2])
            F0   = int(IR[3])
            ENA  = int(IR[4])
            ENB  = int(IR[5])
            INVA = int(IR[6])
            INC  = int(IR[7])

            if SLL8 and SRA1:
                f_log.write("> Error, invalid control signals.\n")
                f_log.write("=" * 60 + "\n")
                PC += 1
                continue

            S, co = executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC)
            Sd = deslocar(S, SLL8, SRA1)
            N, Z = flags_nz(Sd)

            f_log.write(f"b = {int_para_bin32(B)}\n")
            f_log.write(f"a = {int_para_bin32(A)}\n")
            f_log.write(f"s = {int_para_bin32(S)}\n")
            f_log.write(f"sd = {int_para_bin32(Sd)}\n")
            f_log.write(f"n = {N}\n")
            f_log.write(f"z = {Z}\n")
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
        print("Uso: python ula_etapa2_tarefa1.py <arquivo_instrucoes> [A] [B]")
        print()
        print("  arquivo_instrucoes : arquivo .txt com instruções de 8 bits")
        print("  A                  : valor inteiro de A em decimal (padrão: 0)")
        print("  B                  : valor inteiro de B em decimal (padrão: 0)")
        print()
        print("Exemplo: python ula_etapa2_tarefa1.py programa_etapa2_tarefa1.txt 1 2147483648")
        sys.exit(1)

    arquivo_instrucoes = sys.argv[1]
    A = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    B = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    executar_programa(arquivo_instrucoes, A, B)


if __name__ == "__main__":
    main()
