# ====================================
# TRABALHO DE ARQUITETURA 2
# PROFESSORA: SARAH PONTES
# GRUPO: LUÍS FELIPE FAHNING, GUILHERME DE SOUSA, CAIO FIGUEIREDO
# ENTREGAVEL: Interpretador IJVM — ILOAD x, DUP, BIPUSH byte
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

# ── Microinstruções pré-definidas (23 bits: 8 ULA | 9 C-bus | 2 Mem | 4 B-bus) ──
#
# Convenção ULA (8 bits): SLL8 SRA1 F1 F0 ENA ENB INVA INC
# Convenção C-bus (9 bits, da esquerda): H OPC TOS CPP LV SP PC MDR MAR
# Convenção Mem (2 bits): WRITE READ
# Convenção B-bus (4 bits): código decimal do registrador
#
# H = LV  →  Sd = B(LV),  escreve H
MICRO_H_EQ_LV         = "00110100100000000000101"
# H = H+1  →  Sd = A(H)+1,  escreve H
MICRO_H_EQ_H_PLUS1    = "00111001100000000000000"
# MAR = H; rd  →  Sd = A(H),  escreve MAR,  READ
MICRO_MAR_EQ_H_RD     = "00111000000000001010000"
# MAR = SP = SP+1; wr  →  Sd = B(SP)+1,  escreve SP e MAR,  WRITE
MICRO_MAR_SP_PLUS1_WR = "00110101000001001100100"
# TOS = MDR  →  Sd = B(MDR),  escreve TOS
MICRO_TOS_EQ_MDR      = "00110100001000000000000"
# MAR = SP = SP+1  →  Sd = B(SP)+1,  escreve SP e MAR,  sem mem
MICRO_MAR_SP_PLUS1    = "00110101000001001000100"
# MDR = TOS; wr  →  Sd = B(TOS),  escreve MDR,  WRITE
MICRO_MDR_EQ_TOS_WR   = "00110100000000010100111"
# MDR = TOS = H; wr  →  Sd = A(H),  escreve TOS e MDR,  WRITE
MICRO_MDR_TOS_EQ_H_WR = "00111000001000010100000"


def traduzir_instrucao(instrucao):
    """Traduz uma instrução IJVM em lista de microinstruções de 23 bits."""
    tokens = instrucao.strip().split()
    if not tokens:
        return []
    opcode = tokens[0].upper()

    if opcode == 'ILOAD':
        x = int(tokens[1])
        micros = [MICRO_H_EQ_LV]
        for _ in range(x):
            micros.append(MICRO_H_EQ_H_PLUS1)
        micros += [MICRO_MAR_EQ_H_RD, MICRO_MAR_SP_PLUS1_WR, MICRO_TOS_EQ_MDR]
        return micros

    if opcode == 'DUP':
        return [MICRO_MAR_SP_PLUS1, MICRO_MDR_EQ_TOS_WR]

    if opcode == 'BIPUSH':
        byte_str = tokens[1].zfill(8)[:8]
        # caso especial: WRITE=1 e READ=1 → os 8 bits ULA carregam o byte em MBR e H
        fetch = byte_str + "000000000" + "11" + "0000"
        return [MICRO_MAR_SP_PLUS1, fetch, MICRO_MDR_TOS_EQ_H_WR]

    print(f"[AVISO] Instrução IJVM desconhecida: '{instrucao}'")
    return []


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


def escrever_registradores(f_log, regs, indent='  '):
    for nome in ORDEM_LOG:
        f_log.write(f"{indent}{nome.lower()} = {formatar_registrador(nome, regs[nome])}\n")


def escrever_memoria(f_log, memoria, indent='  '):
    for i, val in enumerate(memoria):
        f_log.write(f"{indent}mem[{i}] = {int_para_bin32(val)}\n")


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


def executar_micro(IR, regs, memoria):
    """Executa uma microinstrução de 23 bits, atualiza regs e memoria in-place.
    Retorna lista de strings descrevendo a operação (para o log)."""
    ula_bits  = IR[0:8]
    cbus_bits = IR[8:17]
    mem_bits  = IR[17:19]
    bbus_bits = IR[19:23]

    WRITE = int(mem_bits[0])
    READ  = int(mem_bits[1])

    desc = [f"    ir    = {ula_bits} {cbus_bits} {mem_bits} {bbus_bits}"]

    # Caso especial fetch
    if WRITE and READ:
        byte_val    = int(ula_bits, 2) & 0xFF
        regs['MBR'] = byte_val
        regs['H']   = byte_val
        desc.append(f"    [fetch especial] MBR = H = {int_para_bin32(regs['H'])}")
        return desc

    codigo_b = int(bbus_bits, 2)
    regs_c   = registradores_do_barramento_c(cbus_bits)
    mem_str  = (('WRITE ' if WRITE else '') + ('READ' if READ else '')).strip() or 'none'

    desc.append(f"    b_bus = {DECODIFICADOR_B[codigo_b].lower()}")
    desc.append(f"    c_bus = {', '.join(r.lower() for r in regs_c) if regs_c else 'none'}")
    desc.append(f"    mem   = {mem_str}")

    SLL8 = int(ula_bits[0]); SRA1 = int(ula_bits[1])
    F1   = int(ula_bits[2]); F0   = int(ula_bits[3])
    ENA  = int(ula_bits[4]); ENB  = int(ula_bits[5])
    INVA = int(ula_bits[6]); INC  = int(ula_bits[7])

    A = regs['H'] & MASCARA
    B = valor_barramento_b(codigo_b, regs)

    S, _co = executar_ula(A, B, F0, F1, ENA, ENB, INVA, INC)
    Sd = deslocar(S, SLL8, SRA1)

    for nome in regs_c:
        regs[nome] = Sd & MASCARA

    if WRITE:
        endereco = regs['MAR'] % len(memoria)
        memoria[endereco] = regs['MDR'] & MASCARA
    elif READ:
        endereco = regs['MAR'] % len(memoria)
        regs['MDR'] = memoria[endereco] & MASCARA

    return desc


def executar_programa(arquivo_instrucoes, arquivo_registradores, arquivo_dados, arquivo_log):
    regs    = ler_registradores(arquivo_registradores)
    memoria = ler_memoria(arquivo_dados)

    with open(arquivo_instrucoes, 'r') as f:
        instrucoes_ijvm = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    SEP  = "=" * 62
    SEP2 = "-" * 62

    with open(arquivo_log, 'w') as f_log:
        f_log.write(SEP + "\n")
        f_log.write("  IJVM EXECUTION LOG — Mic-1 Modificada\n")
        f_log.write(SEP + "\n\n")

        f_log.write("> Memory state (initial)\n")
        escrever_memoria(f_log, memoria)
        f_log.write("\n")
        f_log.write("> Register state (initial)\n")
        escrever_registradores(f_log, regs)
        f_log.write("\n" + SEP + "\n\n")

        for idx, instr_ijvm in enumerate(instrucoes_ijvm, 1):
            micros = traduzir_instrucao(instr_ijvm)

            f_log.write(SEP + "\n")
            f_log.write(f"  IJVM [{idx}]: {instr_ijvm}  "
                        f"({len(micros)} microinstrucao{'es' if len(micros) != 1 else ''})\n")
            f_log.write(SEP + "\n\n")

            for m_idx, micro in enumerate(micros, 1):
                f_log.write(f"  Microinstrucao {m_idx}/{len(micros)}\n")
                f_log.write(SEP2 + "\n")
                f_log.write("  Registradores antes:\n")
                escrever_registradores(f_log, regs, indent='    ')
                f_log.write("\n")

                desc_lines = executar_micro(micro, regs, memoria)
                for line in desc_lines:
                    f_log.write(line + "\n")

                f_log.write("\n  Registradores depois:\n")
                escrever_registradores(f_log, regs, indent='    ')
                f_log.write("\n")

            f_log.write(f"  Memoria apos instrucao [{idx}] {instr_ijvm}:\n")
            escrever_memoria(f_log, memoria, indent='    ')
            f_log.write("\n")

        f_log.write(SEP + "\n")
        f_log.write("  Fim do programa.\n")
        f_log.write(SEP + "\n")
        f_log.write("\n> Memory state (final)\n")
        escrever_memoria(f_log, memoria)
        f_log.write("\n> Register state (final)\n")
        escrever_registradores(f_log, regs)

    print(f"Execução concluída. Log salvo em '{arquivo_log}'")


def main():
    if len(sys.argv) < 4:
        print("Uso: python ijvm_entregavel.py <instrucoes> <registradores> <dados>")
        print()
        print("Exemplo: python ijvm_entregavel.py instrucoes.txt "
              "registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt")
        sys.exit(1)

    executar_programa(sys.argv[1], sys.argv[2], sys.argv[3], "saida_entregavel.txt")


if __name__ == "__main__":
    main()
