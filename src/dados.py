"""Tudo que o app.py pede de dado passa por aqui.

A base é a população do IBGE por município, ano, sexo e idade simples
(data/pop_ibge.parquet). A idade vai de 0 a 80, e o 80 quer dizer "80 anos
ou mais": é assim que o arquivo vem.

- o recorte é None (Brasil), a sigla da UF ("SP") ou o município com 6
  dígitos ("355030"), o mesmo código da malha
- sem dado é None/NaN, nunca zero
"""

from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
POPULACAO = RAIZ / "data" / "pop_ibge.parquet"
# Esperança de vida por UF: Projeções da População do IBGE, revisão 2024
# (tab4_indicadores), o mesmo arquivo do painel de Envelhecimento, cortado
# em 2010-2025.
ESPERANCA = RAIZ / "data" / "esperanca_vida_uf.parquet"
# Nascidos vivos por município de residência da mãe, ano e idade da mãe:
# SINASC/DATASUS, gerado por scripts/preparar_nascimentos.py.
NASCIMENTOS = RAIZ / "data" / "nascimentos.parquet"
UFS_IBGE = RAIZ / "data" / "ibge_ufs.parquet"
MALHA_MUNICIPIOS = RAIZ / "geo" / "municipios.parquet"
MALHA_UFS = RAIZ / "geo" / "ufs.parquet"

# o último degrau da idade no arquivo
IDADE_TETO = 80

# faixas de 5 anos da pirâmide, com o 80+ no topo
FAIXAS = [*(f"{i} a {i + 4}" for i in range(0, IDADE_TETO, 5)), f"{IDADE_TETO}+"]

_conexao = None
_trava = threading.Lock()


def _sql(consulta: str, parametros: list | None = None) -> pd.DataFrame:
    """Roda a consulta numa conexão própria da thread (o DuckDB pede isso)."""
    global _conexao
    with _trava:
        if _conexao is None:
            con = duckdb.connect()
            con.execute(f"""
                CREATE VIEW pop AS
                SELECT substr(p.cod_mun, 1, 6) AS cod6,
                       u.sigla AS uf,
                       p.ano,
                       CASE p.sexo WHEN '1' THEN 'M' WHEN '2' THEN 'F' END AS sexo,
                       CAST(p.idade AS INTEGER) AS idade,
                       p.populacao AS n
                FROM read_parquet('{POPULACAO.as_posix()}') p
                JOIN read_parquet('{UFS_IBGE.as_posix()}') u
                  ON CAST(substr(p.cod_mun, 1, 2) AS INTEGER) = u.id
            """)
            if NASCIMENTOS.exists():
                con.execute(f"""
                    CREATE VIEW nasc AS
                    SELECT b.cod6, u.sigla AS uf, CAST(b.ano AS INTEGER) AS ano,
                           CAST(b.idade_mae AS INTEGER) AS idade_mae, b.n
                    FROM read_parquet('{NASCIMENTOS.as_posix()}') b
                    JOIN read_parquet('{UFS_IBGE.as_posix()}') u
                      ON CAST(substr(b.cod6, 1, 2) AS INTEGER) = u.id
                """)
            _conexao = con
    return _conexao.cursor().execute(consulta, parametros or []).df()


def disponivel() -> bool:
    return POPULACAO.exists() and UFS_IBGE.exists()


# ---------------------------------------------------------------------------
# Recorte
# ---------------------------------------------------------------------------

def eh_uf(chave: str | None) -> bool:
    return bool(chave) and len(chave) == 2


def uf_de(chave: str | None) -> str | None:
    """A UF de um recorte: ela mesma, ou a do município."""
    if not chave:
        return None
    if eh_uf(chave):
        return chave
    return _uf_por_codigo().get(chave[:2])


def _onde(recorte: str | None) -> tuple[str, list]:
    if not recorte:
        return "", []
    if eh_uf(recorte):
        return " AND uf = ?", [recorte]
    return " AND cod6 = ?", [recorte]


# ---------------------------------------------------------------------------
# Malhas e nomes
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def territorio() -> gpd.GeoDataFrame:
    """Malha dos municípios: ``cod_mun6``, ``nome_mun``, ``uf``, ``geometry``."""
    return gpd.read_parquet(MALHA_MUNICIPIOS)


@lru_cache(maxsize=1)
def ufs() -> gpd.GeoDataFrame:
    """Malha dos estados: ``uf``, ``nome_uf``, ``geometry``."""
    return gpd.read_parquet(MALHA_UFS)


def municipios_da_uf(uf: str) -> gpd.GeoDataFrame:
    malha = territorio()
    return malha[malha["uf"] == uf].reset_index(drop=True)


@lru_cache(maxsize=1)
def _uf_por_codigo() -> dict[str, str]:
    u = pd.read_parquet(UFS_IBGE)
    return {str(i): s for i, s in zip(u["id"], u["sigla"], strict=True)}


@lru_cache(maxsize=1)
def _nomes_uf() -> dict[str, str]:
    u = ufs()
    return dict(zip(u["uf"], u["nome_uf"], strict=True))


@lru_cache(maxsize=1)
def _nomes_mun() -> dict[str, str]:
    m = territorio()
    return dict(zip(m["cod_mun6"], m["nome_mun"], strict=True))


def nome_uf(uf: str) -> str:
    return _nomes_uf().get(uf, uf)


def nome(recorte: str | None, territorio_inteiro: str = "Brasil") -> str:
    """Nome para a tela: "Brasil", "São Paulo" ou "Campinas (SP)"."""
    if not recorte:
        return territorio_inteiro
    if eh_uf(recorte):
        return nome_uf(recorte)
    return f"{_nomes_mun().get(recorte, recorte)} ({uf_de(recorte)})"


# ---------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------

# Uma conta só para tudo: soma por grupo e idade, e daí sai cada indicador.
# A mediana interpola dentro da idade simples (a idade `a` cobre [a, a+1)).
_INDICADORES = """
WITH base AS (
    SELECT {grupo} AS grupo, idade, sexo, sum(n) AS n
    FROM pop WHERE {filtro_ano} {onde}
    GROUP BY ALL
),
por_idade AS (
    SELECT grupo, idade, sum(n) AS n FROM base GROUP BY ALL
),
acumulado AS (
    SELECT grupo, idade, n,
           sum(n) OVER (PARTITION BY grupo ORDER BY idade) AS cum,
           sum(n) OVER (PARTITION BY grupo) AS tot
    FROM por_idade
),
mediana AS (
    SELECT grupo,
           arg_min(idade + (tot / 2.0 - (cum - n)) / n, idade) FILTER (WHERE cum >= tot / 2.0)
               AS idade_mediana
    FROM acumulado WHERE n > 0
    GROUP BY grupo
)
SELECT b.grupo,
       sum(n) AS populacao,
       100.0 * sum(n) FILTER (WHERE idade < 15) / nullif(sum(n), 0) AS pct_0_14,
       100.0 * sum(n) FILTER (WHERE idade BETWEEN 15 AND 64) / nullif(sum(n), 0) AS pct_15_64,
       100.0 * sum(n) FILTER (WHERE idade >= 65) / nullif(sum(n), 0) AS pct_65,
       100.0 * sum(n) FILTER (WHERE idade >= 60) / nullif(sum(n), 0) AS pct_60,
       100.0 * sum(n) FILTER (WHERE idade >= 60)
             / nullif(sum(n) FILTER (WHERE idade < 15), 0) AS indice_envelhecimento,
       100.0 * (coalesce(sum(n) FILTER (WHERE idade < 15), 0)
                + coalesce(sum(n) FILTER (WHERE idade >= 65), 0))
             / nullif(sum(n) FILTER (WHERE idade BETWEEN 15 AND 64), 0) AS razao_dependencia,
       100.0 * coalesce(sum(n) FILTER (WHERE idade < 15), 0)
             / nullif(sum(n) FILTER (WHERE idade BETWEEN 15 AND 64), 0) AS dependencia_jovem,
       100.0 * coalesce(sum(n) FILTER (WHERE idade >= 65), 0)
             / nullif(sum(n) FILTER (WHERE idade BETWEEN 15 AND 64), 0) AS dependencia_idosa,
       100.0 * sum(n) FILTER (WHERE sexo = 'M')
             / nullif(sum(n) FILTER (WHERE sexo = 'F'), 0) AS razao_sexo,
       any_value(m.idade_mediana) AS idade_mediana
FROM base b LEFT JOIN mediana m USING (grupo)
GROUP BY b.grupo
"""


def _indicadores(grupo: str, ano: int | None, recorte: str | None = None) -> pd.DataFrame:
    """``ano=None`` pega todos os anos (para agrupar por ``ano``)."""
    onde, parametros = _onde(recorte)
    filtro_ano, anos_param = ("ano = ?", [ano]) if ano is not None else ("true", [])
    return _sql(_INDICADORES.format(grupo=grupo, onde=onde, filtro_ano=filtro_ano),
                [*anos_param, *parametros])


# Área: sai da própria malha, numa projeção de área igual (Albers da América
# do Sul). Estado e Brasil são a soma dos municípios, então batem entre si.
@lru_cache(maxsize=1)
def _area_municipios() -> pd.Series:
    """km² por município (``cod_mun6``)."""
    malha = territorio()
    area = malha.to_crs("ESRI:102033").area / 1e6
    return pd.Series(area.values, index=malha["cod_mun6"].values)


def _area(grupo: str, recorte: str | None = None) -> pd.Series:
    """km² por grupo da consulta: o município, a UF, ou o 'total' do recorte."""
    mun = _area_municipios()
    if grupo == "cod6":
        return mun
    ufs_mun = mun.index.map(lambda c: uf_de(c))
    if grupo == "uf":
        return mun.groupby(ufs_mun).sum()
    if not recorte:
        total = mun.sum()
    elif eh_uf(recorte):
        total = mun[ufs_mun == recorte].sum()
    else:
        total = mun.get(recorte, float("nan"))
    return pd.Series({"total": total})


# Nascimentos. A taxa de fecundidade total (TFT) é 5 vezes a soma das taxas
# por faixa de 5 anos da mãe, de 15 a 49. As mães de 10 a 14 entram na faixa
# 15-19 e as de 50+ na 45-49 (senão esses nascimentos sumiriam da conta), e os
# de idade ignorada são distribuídos na proporção dos outros.
_NASCIMENTOS = """
WITH b AS (
    SELECT {grupo} AS grupo, idade_mae, n FROM nasc WHERE {filtro_ano} {onde}
),
por_faixa AS (
    SELECT grupo, least(greatest(idade_mae // 5, 3), 9) AS faixa, sum(n) AS n
    FROM b WHERE idade_mae IS NOT NULL GROUP BY ALL
),
mulheres AS (
    SELECT {grupo} AS grupo, idade // 5 AS faixa, sum(n) AS m
    FROM pop WHERE {filtro_ano} {onde} AND sexo = 'F' AND idade BETWEEN 15 AND 49
    GROUP BY ALL
),
tft AS (
    SELECT p.grupo, 5 * sum(p.n / nullif(w.m, 0)) AS tft_conhecida
    FROM por_faixa p JOIN mulheres w USING (grupo, faixa)
    GROUP BY p.grupo
)
SELECT b.grupo,
       sum(n) AS nascidos,
       100.0 * sum(n) FILTER (WHERE idade_mae < 20) / nullif(sum(n) FILTER (WHERE idade_mae IS NOT NULL), 0)
           AS pct_maes_adolescentes,
       sum(idade_mae * n) / nullif(sum(n) FILTER (WHERE idade_mae IS NOT NULL), 0) AS idade_media_mae,
       any_value(t.tft_conhecida)
           * sum(n) / nullif(sum(n) FILTER (WHERE idade_mae IS NOT NULL), 0) AS fecundidade
FROM b LEFT JOIN tft t USING (grupo)
GROUP BY b.grupo
"""

COLUNAS_NASCIMENTOS = ("nascidos", "natalidade", "fecundidade", "idade_media_mae", "pct_maes_adolescentes")


def tem_nascimentos() -> bool:
    return NASCIMENTOS.exists()


@lru_cache(maxsize=1)
def anos_nascimentos() -> list[int]:
    if not tem_nascimentos():
        return []
    return sorted(int(a) for a in _sql("SELECT DISTINCT ano FROM nasc")["ano"])


def _nascimentos(grupo: str, ano: int | None, recorte: str | None) -> pd.DataFrame:
    """Nascimentos por grupo; vazio quando o ano não está no SINASC."""
    if not tem_nascimentos() or (ano is not None and ano not in anos_nascimentos()):
        return pd.DataFrame(columns=["grupo", *COLUNAS_NASCIMENTOS]).set_index("grupo")
    onde, parametros = _onde(recorte)
    filtro_ano, anos_param = ("ano = ?", [ano]) if ano is not None else ("true", [])
    # o mesmo filtro entra duas vezes: nos nascimentos e nas mulheres
    tabela = _sql(_NASCIMENTOS.format(grupo=grupo, onde=onde, filtro_ano=filtro_ano),
                  [*anos_param, *parametros, *anos_param, *parametros])
    return tabela.set_index("grupo")


COLUNAS_ESPERANCA = {"e0_T": "esperanca_vida", "e0_H": "esperanca_vida_h", "e0_M": "esperanca_vida_m"}


@lru_cache(maxsize=1)
def _esperanca_uf() -> pd.DataFrame:
    """Esperança de vida ao nascer por UF e ano: total, homens e mulheres."""
    tabela = pd.read_parquet(ESPERANCA)
    tabela["ano"] = tabela["ano"].astype(int)
    return tabela.rename(columns=COLUNAS_ESPERANCA).set_index(["uf", "ano"])[list(COLUNAS_ESPERANCA.values())]


def esperanca_estimada(recorte: str | None) -> bool:
    """Se o número é a média dos estados (Brasil) e não o publicado pelo IBGE."""
    return not recorte


def esperanca_herdada(recorte: str | None) -> bool:
    """Se o número é o do estado, mostrado num município."""
    return bool(recorte) and not eh_uf(recorte)


def _esperanca(ano: int, recorte: str | None) -> dict[str, float]:
    """A esperança de vida de um recorte.

    O IBGE não calcula por município: o município fica com o número do
    estado. Para o Brasil, o arquivo só tem as UFs, então o número é a média
    delas ponderada pela população do ano (o mesmo critério do painel de
    Envelhecimento) — uma aproximação, e a tela avisa.
    """
    tabela = _esperanca_uf()
    if recorte:
        chave = (uf_de(recorte), ano)
        return tabela.loc[chave].to_dict() if chave in tabela.index else {}
    if ano not in tabela.index.get_level_values("ano"):
        return {}
    do_ano = tabela.xs(ano, level="ano")
    pesos = _indicadores("uf", ano).set_index("grupo")["populacao"].reindex(do_ano.index)
    return {c: float((do_ano[c] * pesos).sum() / pesos.sum()) for c in do_ano.columns}


def _tabela(grupo: str, ano: int, recorte: str | None = None) -> pd.DataFrame:
    """Os indicadores da consulta, mais os que precisam de fora dela.

    - ``crescimento``: % de mudança da população desde o ano anterior
      (vazio no primeiro ano da base)
    - ``densidade``: habitantes por km²
    """
    tabela = _indicadores(grupo, ano, recorte).set_index("grupo")
    if ano - 1 in anos():
        antes = _indicadores(grupo, ano - 1, recorte).set_index("grupo")["populacao"]
        tabela["crescimento"] = (tabela["populacao"] / antes.reindex(tabela.index) - 1) * 100
    else:
        tabela["crescimento"] = float("nan")
    tabela["densidade"] = tabela["populacao"] / _area(grupo, recorte).reindex(tabela.index)
    # esperança de vida: o estado; o município herda o do estado
    if grupo == "'total'":
        for coluna, valor in _esperanca(ano, recorte).items():
            tabela[coluna] = valor
    else:
        esp = _esperanca_uf()
        do_ano = esp.xs(ano, level="ano") if ano in esp.index.get_level_values("ano") else esp.iloc[0:0]
        ufs_grupo = tabela.index if grupo == "uf" else tabela.index.map(lambda c: uf_de(c))
        for coluna in COLUNAS_ESPERANCA.values():
            tabela[coluna] = do_ano[coluna].reindex(ufs_grupo).to_numpy() if not do_ano.empty else float("nan")
    return _com_nascimentos(tabela, _nascimentos(grupo, ano, recorte))


def _com_nascimentos(tabela: pd.DataFrame, nasc: pd.DataFrame) -> pd.DataFrame:
    """Junta os nascimentos e calcula a natalidade (por mil habitantes)."""
    for coluna in COLUNAS_NASCIMENTOS:
        if coluna != "natalidade":
            tabela[coluna] = nasc[coluna].reindex(tabela.index).astype(float) if coluna in nasc else float("nan")
    tabela["natalidade"] = tabela["nascidos"] / tabela["populacao"] * 1000
    return tabela


@lru_cache(maxsize=1)
def anos() -> list[int]:
    return sorted(int(a) for a in _sql("SELECT DISTINCT ano FROM pop")["ano"])


def kpis(ano: int, recorte: str | None = None) -> dict[str, float | None]:
    """Os indicadores de um recorte num ano."""
    if ano not in anos():
        return {}
    tabela = _tabela("'total'", ano, recorte)
    if tabela.empty:
        return {}
    linha = tabela.iloc[0]
    return {k: (None if pd.isna(v) else float(v)) for k, v in linha.items()}


def valores(metrica: str, ano: int, nivel: str, uf: str | None = None) -> pd.Series:
    """A métrica por estado (``nivel="UF"``) ou por município (``"MUN"``).

    ``uf`` limita os municípios aos de um estado.
    """
    grupo = "uf" if nivel == "UF" else "cod6"
    tabela = _tabela(grupo, ano, uf if nivel == "MUN" else None)
    return tabela[metrica].astype(float)


def serie(recorte: str | None = None) -> pd.DataFrame:
    """Todos os indicadores, um ano por linha, numa consulta só."""
    tabela = _indicadores("ano", None, recorte).rename(columns={"grupo": "ano"})
    tabela["ano"] = tabela["ano"].astype(int)
    tabela = tabela.sort_values("ano").reset_index(drop=True)
    tabela["crescimento"] = tabela["populacao"].pct_change() * 100
    tabela["densidade"] = tabela["populacao"] / float(_area("'total'", recorte).iloc[0])
    esperanca = pd.DataFrame([{"ano": a, **_esperanca(a, recorte)} for a in tabela["ano"]])
    tabela = tabela.merge(esperanca, on="ano", how="left").set_index("ano")
    nasc = _nascimentos("ano", None, recorte)
    nasc.index = nasc.index.astype(int)
    return _com_nascimentos(tabela, nasc).reset_index()


def serie_anual(metrica: str, recorte: str | None = None) -> pd.DataFrame:
    """``ano`` e ``valor`` da métrica, de ponta a ponta da base."""
    return serie(recorte)[["ano", metrica]].rename(columns={metrica: "valor"})


def ranking(metrica: str, ano: int, nivel: str, uf: str | None = None) -> pd.DataFrame:
    """``chave``, ``nome`` e ``valor``, do maior para o menor."""
    serie = valores(metrica, ano, nivel, uf).dropna().sort_values(ascending=False)
    nomes = _nomes_uf() if nivel == "UF" else _nomes_mun()
    return pd.DataFrame({
        "chave": serie.index,
        "nome": [nomes.get(c, c) for c in serie.index],
        "valor": serie.values,
    })


def piramide(ano: int, recorte: str | None = None, proporcao: bool = False) -> pd.DataFrame:
    """``faixa_etaria``, ``faixa_ord``, ``sexo`` e ``valor``, no formato do core.

    Com ``proporcao``, o valor é o % da população do recorte (homens e
    mulheres somam 100), o que deixa comparar recortes de tamanhos diferentes.
    """
    onde, parametros = _onde(recorte)
    tabela = _sql(f"""
        SELECT least(idade // 5, {IDADE_TETO // 5}) AS faixa_ord, sexo, sum(n) AS valor
        FROM pop WHERE ano = ? {onde}
        GROUP BY ALL ORDER BY faixa_ord, sexo
    """, [ano, *parametros])
    if tabela.empty:
        return tabela.assign(faixa_etaria=pd.Series(dtype=str))
    tabela["faixa_ord"] = tabela["faixa_ord"].astype(int)
    tabela["faixa_etaria"] = tabela["faixa_ord"].map(dict(enumerate(FAIXAS)))
    tabela["valor"] = tabela["valor"].astype(float)
    if proporcao:
        tabela["valor"] = tabela["valor"] / tabela["valor"].sum() * 100
    return tabela
