Etapa 1 — ULA 6 bits
python3 ula_etapa1.py programa_etapa1.txt -1 1
# Gera: saida_etapa1.txt
# Argumentos: arquivo, valor de A, valor de B

---
Etapa 2 — Tarefa 1: ULA 8 bits
python3 ula_etapa2_tarefa1.py programa_etapa2_tarefa1.txt 1 2147483648
# Gera: saida_etapa2_tarefa1.txt
# Argumentos: arquivo, A=1, B=MIN_INT

---
Etapa 2 — Tarefa 2: Caminho de dados
python3 datapath_etapa2_tarefa2.py programa_etapa2_tarefa2.txt registradores_etapa2_tarefa2.txt
# Gera: saida_etapa2_tarefa2.txt
# Argumentos: microinstruções (21 bits), estado inicial dos registradores

---
Etapa 3 — Tarefa 1: Mic-1 com memória
python3 mic1_etapa3_tarefa1.py microinstrucoes_etapa3_tarefa1.txt registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt
# Gera: saida_etapa3_tarefa1.txt
# Argumentos: microinstruções (23 bits), registradores, memória inicial

---
Entregável — Interpretador IJVM
python3 ijvm_entregavel.py instrucoes.txt registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt
# Gera: saida_entregavel.txt
# Argumentos: instruções IJVM (BIPUSH/DUP/ILOAD), registradores, memória

---
Os arquivos de saída (saida_*.txt) são sobrescritos a cada execução. Se quiser rodar tudo de uma vez:

python3 ula_etapa1.py programa_etapa1.txt -1 1 && \
python3 ula_etapa2_tarefa1.py programa_etapa2_tarefa1.txt 1 2147483648 && \
python3 datapath_etapa2_tarefa2.py programa_etapa2_tarefa2.txt registradores_etapa2_tarefa2.txt && \
python3 mic1_etapa3_tarefa1.py microinstrucoes_etapa3_tarefa1.txt registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt && \
python3 ijvm_entregavel.py instrucoes.txt registradores_etapa3_tarefa1.txt dados_etapa3_tarefa1.txt
