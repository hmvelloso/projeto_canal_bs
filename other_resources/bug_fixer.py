import os

PASTA_CSV = "../jogos"

for nome_arquivo in os.listdir(PASTA_CSV):
    if not nome_arquivo.lower().endswith(".csv"):
        continue

    caminho = os.path.join(PASTA_CSV, nome_arquivo)

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    # processa só as 4 primeiras linhas
    for i in range(min(4, len(linhas))):
        linha = linhas[i].rstrip("\n")

        # remove espaços à direita antes de checar
        linha_sem_espaco = linha.rstrip()

        if not linha_sem_espaco.endswith(","):
            linhas[i] = linha_sem_espaco + ",\n"
        else:
            linhas[i] = linha + "\n" if not linha.endswith("\n") else linha

    with open(caminho, "w", encoding="utf-8") as f:
        f.writelines(linhas)

    print(f"✔ Arquivo ajustado: {nome_arquivo}")