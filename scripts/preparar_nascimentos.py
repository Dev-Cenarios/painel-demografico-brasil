"""Gera data/nascimentos.parquet a partir do SINASC (DATASUS).

Roda uma vez, quando o DATASUS fechar um ano novo. O painel não lê DBC: lê o
parquet que este script escreve.

    python scripts/preparar_nascimentos.py <pasta de trabalho> [ano_inicial ano_final]

Para cada ano, baixa o arquivo nacional `DNBR<ano>.dbc` do FTP do DATASUS
(SINASC/1996_/Dados/DNRES, os anos consolidados), soma os nascidos vivos por
**município de residência da mãe** e **idade da mãe**, e apaga o DBC e o DBF
antes do ano seguinte: são ~2,3 GB de 2010 a 2024, e só a soma fica.

Precisa do `pyreaddbc`, que tem wheel para Python 3.11 e 3.12 (no 3.13+ ele
tenta compilar e falha no Windows). Por isso este script roda num ambiente à
parte do painel, que nunca precisa dele.

Cuidados:

- **O arquivo do ano é o ano do nascimento** (DTNASC), não o do registro.
- **`IDADEMAE` 99 é "ignorado"**, e idade fora de 10 a 59 é erro de digitação:
  as duas viram vazio. O nascimento continua contado; só não entra nas contas
  que usam a idade da mãe.
- **`CODMUNRES` com 7 dígitos** (alguns anos) é cortado para os 6 do resto do
  painel. Código terminado em 0000 é "município ignorado" da UF e fica de fora
  do mapa, mas entra no total da UF e do Brasil.
"""

from __future__ import annotations

import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pyreaddbc

FTP = "ftp://ftp.datasus.gov.br/dissemin/publicos/SINASC/1996_/Dados/DNRES/DNBR{ano}.dbc"
DESTINO = Path(__file__).resolve().parents[1] / "data" / "nascimentos.parquet"
COLUNAS = ("CODMUNRES", "IDADEMAE")


def ler_dbf(caminho: Path, colunas: tuple[str, ...]) -> pd.DataFrame:
    """Lê só as colunas pedidas de um DBF, direto dos bytes (rápido e sem dependência).

    O DBF é de largura fixa: o cabeçalho diz onde cada campo começa, e o
    resto é recorte de bytes.
    """
    with open(caminho, "rb") as f:
        cabeca = f.read(32)
        n, tam_cabeca, tam_registro = struct.unpack("<IHH", cabeca[4:12])
        campos, deslocamento = {}, 1  # o byte 0 do registro é a marca de apagado
        while True:
            desc = f.read(32)
            if desc[0] == 0x0D:
                break
            nome = desc[:11].split(b"\x00")[0].decode("ascii").strip().upper()
            largura = desc[16]
            campos[nome] = (deslocamento, largura)
            deslocamento += largura
    registros = np.memmap(caminho, dtype=np.uint8, mode="r", offset=tam_cabeca, shape=(n, tam_registro))
    ativos = registros[:, 0] != ord("*")
    saida = {}
    for coluna in colunas:
        inicio, largura = campos[coluna]
        bruto = np.ascontiguousarray(registros[ativos, inicio:inicio + largura]).view(f"S{largura}").ravel()
        saida[coluna] = pd.Series(bruto).str.decode("latin-1").str.strip()
    del registros
    return pd.DataFrame(saida)


def somar_ano(ano: int, pasta: Path) -> pd.DataFrame:
    dbc, dbf = pasta / f"DNBR{ano}.dbc", pasta / f"DNBR{ano}.dbf"
    try:
        t = time.time()
        urllib.request.urlretrieve(FTP.format(ano=ano), dbc)
        baixado = time.time() - t
        pyreaddbc.dbc2dbf(str(dbc), str(dbf))
        dn = ler_dbf(dbf, COLUNAS)
    finally:
        for arquivo in (dbc, dbf):
            arquivo.unlink(missing_ok=True)

    idade = pd.to_numeric(dn["IDADEMAE"], errors="coerce")
    dn["idade_mae"] = idade.where(idade.between(10, 59)).astype("Int16")
    dn["cod6"] = dn["CODMUNRES"].str[:6]
    soma = (dn.groupby(["cod6", "idade_mae"], dropna=False).size()
            .rename("n").reset_index().assign(ano=ano))
    print(f"{ano}: {len(dn):,} nascidos vivos · baixado em {baixado:.0f}s · "
          f"idade da mãe vazia em {dn['idade_mae'].isna().mean():.2%}", flush=True)
    return soma


def main() -> None:
    pasta = Path(sys.argv[1])
    inicio, fim = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (2010, 2024)
    pasta.mkdir(parents=True, exist_ok=True)
    partes = [somar_ano(ano, pasta) for ano in range(inicio, fim + 1)]
    tabela = pd.concat(partes, ignore_index=True)[["cod6", "ano", "idade_mae", "n"]]
    tabela["ano"] = tabela["ano"].astype("int16")
    tabela["n"] = tabela["n"].astype("int32")
    tabela.to_parquet(DESTINO, index=False)
    print(f"escrito {DESTINO} · {len(tabela):,} linhas · {tabela['n'].sum():,} nascidos vivos")


if __name__ == "__main__":
    main()
