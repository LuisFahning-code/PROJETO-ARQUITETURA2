# ====================================
# TRABALHO DE ARQUITETURA 2
# PROFESSORA: SARAH PONTES
# GRUPO: LUÍS FELIPE FAHNING, GUILHERME DE SOUSA, CAIO FIGUEIREDO
# ETAPA 3 - TAREFA 1: Mic-1 com acesso à memória (microinstruções de 23 bits)
import sys

from ula_etapa1 import executar_ula, int_para_bin32
from ula_etapa2_tarefa1 import deslocar

MASCARA = 0xFFFFFFFF
ORDEM_LOG = ['MAR', 'MDR', 'PC', 'MBR', 'SP', 'LV', 'CPP', 'TOS', 'OPC', 'H']

DECODIFICADOR_B = {
    8: 'OPC', 7: 'TOS', 6: 'CPP', 5: 'LV', 4: 'SP',
    3: 'MBRU', 2: 'MBR', 1: 'PC', 0: 'MDR',
}

SELETOR_C = {8: 'H', 7: 'OPC', 6: 'TOS', 5: 'CPP', 4: 'LV', 3: 'SP', 2: 'PC', 1: 'MDR', 0: 'MAR'}


def ler_registradores(arquivo):
    regs = {}
    with open(arquivo, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            nome, valor = linha.split('=')
            regs[nome.strip().upper()] = int(valor.strip(), 2)
    return regs


def ler_memoria(arquivo):
    memoria = []
    with open(arquivo, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith('#'):
                memoria.append(int(linha, 2))
    return memoria


def formatar_registrador(nome, valor):
    if nome == 'MBR':
        return format(valor & 0xFF, '08b')
    return int_para_bin32(valor)


def escrever_registradores(f_log, regs, indent=''):
    for nome in ORDEM_LOG:
        f_log.write(f"{indent}{nome.lower()} = {formatar_registrador(nome, regs[nome])}\n")


def escrever_memoria(f_log, memoria, indent=''):
    f_log.write(f"{indent}> Memory\n")
    for i, val in enumerate(memoria):
        f_log.write(f"{indent}  mem[{i}] = {int_para_bin32(val)}\n")


def valor_barramento_b(codigo, regs):
    nome = DECODIFICADOR_B[codigo]
    if nome == 'MBR':
        v = regs['MBR'] & 0xFF
        if v & 0x80:
            v -= 256
        return v & MASCARA
    if nome == 'MBRU':
        return regs['MBR'] & 0xFF
    return regs[nome] & MASCARA


def registradores_do_barramento_c(cbus_bits):
    return [SELETOR_C[8 - i] for i, c in enumerate(cbus_bits) if c == '1']


def executar_programa(arquivo_instrucoes, arquivo_registradores, arquivo_dados, arquivo_log):
    regs    = ler_registradores(arquivo_registradores)
    memoria = ler_memoria(arquivo_dados)

    with open(arquivo_instrucoes, 'r') as f_instrucoes, \
         open(arquivo_log, 'w') as f_log:

        instrucoes = [l.strip() for l in f_instrucoes
                      if l.strip() and not l.startswith('#')]

        for instr in instrucoes:
            f_log.write(instr + "\n")
        f_log.write("\n")

        SEP = "=" * 57
        f_log.write(SEP + "\n")
        f_log.write("> Initial register states\n")
        escrever_registradores(f_log, regs)
        f_log.write("\n")
        escrever_memoria(f_log, memoria)
        f_log.write(SEP + "\n")
        f_log.write("Start of program\n")
        f_log.write(SEP + "\n")

        ciclo = 0
        for IR in instrucoes:
            if len(IR) != 23 or not all(c in '01' for c in IR):
                print(f"[AVISO] Instrução inválida: '{IR}' — ignorada")
                continue

            ciclo += 1
            ula_bits  = IR[0:8]
            cbus_bits = IR[8:17]
            mem_bits  = IR[17:19]
            bbus_bits = IR[19:23]

            WRITE = int(mem_bits[0])
            READ  = int(mem_bits[1])

            f_log.write(f"Cycle {ciclo}\n")
            f_log.write(f"ir = {ula_bits} {cbus_bits} {mem_bits} {bbus_bits}\n\n")

            # Caso especial: WRITE=1 e READ=1 → fetch (carrega byte em MBR e H)
            if WRITE and READ:
                byte_val    = int(ula_bits, 2) & 0xFF
                regs['MBR'] = byte_val
                regs['H']   = byte_val          # zero-extended para 32 bits
                f_log.write(f"> Special fetch: MBR = H = {int_para_bin32(regs['H'])}\n\n")
                f_log.write("> Registers after instruction\n")
                escrever_registradores(f_log, regs)
                f_log.write("\n")
                escrever_memoria(f_log, memoria)
                f_log.write(SEP + "\n")
                continue

            codigo_b = int(bbus_bits, 2)
            regs_c   = registradores_do_barramento_c(cbus_bits)
            mem_str  = (('WRITE ' if WRITE else '') + ('READ' if READ else '')).strip() or 'none'

            f_log.write(f"b_bus = {DECODIFICADOR_B[codigo_b].lower()}\n")
            f_log.write(f"c_bus = {', '.join(r.lower() for r in regs_c) if regs_c else 'none'}\n")
            f_log.write(f"mem   = {mem_str}\n\n")

            f_log.write("> Registers before instruction\n")
            escrever_registradores(f_log, regs)
            f_log.write("\n")

            # Decodificação da ULA — formato: SLL8 SRA1 F1 F0 ENA ENB INVA INC
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

            S, _co = executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC)
            Sd = deslocar(S, SLL8, SRA1)

            # Escrita no barramento C
            for nome in regs_c:
                regs[nome] = Sd & MASCARA

            # Operações de memória (após C-bus)
            if WRITE:
                endereco = regs['MAR'] % len(memoria)
                memoria[endereco] = regs['MDR'] & MASCARA
            elif READ:
                endereco = regs['MAR'] % len(memoria)
                regs['MDR'] = memoria[endereco] & MASCARA

            f_log.write("> Registers after instruction\n")
            escrever_registradores(f_log, regs)
            f_log.write("\n")
            escrever_memoria(f_log, memoria)
            f_log.write(SEP + "\n")

        f_log.write(f"Cycle {ciclo + 1}\n")
        f_log.write("No more lines, EOP.\n")

    print(f"Execução concluída. Log salvo em '{arquivo_log}'")


def main():
    if len(sys.argv) < 4:
        print("Uso: python mic1_etapa3_tarefa1.py <microinstrucoes> <registradores> <dados>")
        print()
        print("Exemplo: python mic1_etapa3_tarefa1.py microinstrucoes_etapa3_tarefa1.txt "
              "registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt")
        sys.exit(1)

    executar_programa(sys.argv[1], sys.argv[2], sys.argv[3], "saida_etapa3_tarefa1.txt")


if __name__ == "__main__":
    main()
