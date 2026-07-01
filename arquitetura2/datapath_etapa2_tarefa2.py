# ====================================
# TRABALHO DE ARQUITETURA 2
# PROFESSORA: SARAH PONTES
# GRUPO: LUÍS FELIPE FAHNING, GUILHERME DE SOUSA, CAIO FIGUEIREDO
# ETAPA 2 - TAREFA 2: Caminho de dados da Mic-1 (registradores, decodificador e seletor)
import sys

from ula_etapa1 import executar_ula, int_para_bin32
from ula_etapa2_tarefa1 import deslocar

MASCARA = 0xFFFFFFFF

# Ordem de impressão dos registradores no log (mesma do arquivo de estado inicial)
ORDEM_LOG = ['MAR', 'MDR', 'PC', 'MBR', 'SP', 'LV', 'CPP', 'TOS', 'OPC', 'H']

# Decodificador de 4 bits: código -> registrador que comanda o barramento B
DECODIFICADOR_B = {
    8: 'OPC', 7: 'TOS', 6: 'CPP', 5: 'LV', 4: 'SP',
    3: 'MBRU', 2: 'MBR', 1: 'PC', 0: 'MDR',
}

# Seletor de 9 bits: posição do bit -> registrador habilitado para escrita no barramento C
SELETOR_C = {8: 'H', 7: 'OPC', 6: 'TOS', 5: 'CPP', 4: 'LV', 3: 'SP', 2: 'PC', 1: 'MDR', 0: 'MAR'}


def ler_registradores(arquivo):
    regs = {}
    with open(arquivo, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            nome, valor = linha.split('=')
            regs[nome.strip().upper()] = int(valor.strip(), 2)
    return regs


def formatar_registrador(nome, valor):
    if nome == 'MBR':
        return format(valor & 0xFF, '08b')
    return int_para_bin32(valor)


def escrever_registradores(f_log, regs):
    for nome in ORDEM_LOG:
        f_log.write(f"{nome.lower()} = {formatar_registrador(nome, regs[nome])}\n")


def valor_barramento_b(codigo, regs):
    nome = DECODIFICADOR_B[codigo]
    if nome == 'MBR':
        # MBR: estendido até 32 bits com o bit de sinal (bit mais alto do byte)
        v = regs['MBR'] & 0xFF
        if v & 0x80:
            v -= 256
        return v & MASCARA
    if nome == 'MBRU':
        # MBRU: estendido até 32 bits com zeros
        return regs['MBR'] & 0xFF
    return regs[nome] & MASCARA


def registradores_do_barramento_c(cbus_bits):
    # cbus_bits tem 9 caracteres: bit 8 (H) até bit 0 (MAR), da esquerda para a direita
    return [SELETOR_C[8 - i] for i, c in enumerate(cbus_bits) if c == '1']


def executar_programa(arquivo_instrucoes, arquivo_registradores, arquivo_log="saida_etapa2_tarefa2.txt"):
    regs = ler_registradores(arquivo_registradores)

    with open(arquivo_instrucoes, 'r') as f_instrucoes, \
         open(arquivo_log, 'w') as f_log:

        instrucoes = [l.strip() for l in f_instrucoes if l.strip()]

        for instrucao in instrucoes:
            f_log.write(instrucao + "\n")
        f_log.write("\n")
        f_log.write("=" * 53 + "\n")
        f_log.write("> Initial register states\n")
        escrever_registradores(f_log, regs)
        f_log.write("\n")
        f_log.write("=" * 53 + "\n")
        f_log.write("Start of program\n")
        f_log.write("=" * 53 + "\n")

        ciclo = 0
        for IR in instrucoes:
            if len(IR) != 21 or not all(c in '01' for c in IR):
                print(f"[AVISO] Instrução inválida: '{IR}' — ignorada")
                continue

            ciclo += 1

            ula_bits = IR[0:8]
            cbus_bits = IR[8:17]
            bbus_bits = IR[17:21]

            f_log.write(f"Cycle {ciclo}\n")
            f_log.write(f"ir = {ula_bits} {cbus_bits} {bbus_bits}\n\n")

            codigo_b = int(bbus_bits, 2)
            regs_c = registradores_do_barramento_c(cbus_bits)

            f_log.write(f"b_bus = {DECODIFICADOR_B[codigo_b].lower()}\n")
            f_log.write(f"c_bus = {', '.join(r.lower() for r in regs_c) if regs_c else 'nenhum'}\n\n")

            f_log.write("> Registers before instruction\n")
            escrever_registradores(f_log, regs)
            f_log.write("\n")

            # Decodificação da ULA — formato: SLL8 SRA1 F0 F1 ENA ENB INVA INC
            SLL8 = int(ula_bits[0])
            SRA1 = int(ula_bits[1])
            F1   = int(ula_bits[2])
            F0   = int(ula_bits[3])
            ENA  = int(ula_bits[4])
            ENB  = int(ula_bits[5])
            INVA = int(ula_bits[6])
            INC  = int(ula_bits[7])

            A = regs['H'] & MASCARA
            B = valor_barramento_b(codigo_b, regs)

            S, co = executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC)
            Sd = deslocar(S, SLL8, SRA1)

            for nome in regs_c:
                regs[nome] = Sd & MASCARA

            f_log.write("> Registers after instruction\n")
            escrever_registradores(f_log, regs)
            f_log.write("=" * 53 + "\n")

        f_log.write(f"Cycle {ciclo}\n")
        f_log.write("No more lines, EOP.\n")

    print(f"Execução concluída. Log salvo em '{arquivo_log}'")


def main():
    if len(sys.argv) < 3:
        print("Uso: python datapath_etapa2_tarefa2.py <arquivo_instrucoes> <arquivo_registradores>")
        print()
        print("Exemplo: python datapath_etapa2_tarefa2.py programa_etapa2_tarefa2.txt registradores_etapa2_tarefa2.txt")
        sys.exit(1)

    executar_programa(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
