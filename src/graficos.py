"""Gráficos deste painel, feitos em cima dos do cenarios_core.

O core desenha a pirâmide e as séries; aqui só o que é de demografia: a
pirâmide com o contorno de outro ano por cima, e os grandes grupos de idade.
"""

from __future__ import annotations

from html import escape

import pandas as pd
from cenarios_core import grafico_componente as gc

from src import estilo
from src import indicadores as ind

COR_CONTORNO = "#111827"


def piramide(atual: pd.DataFrame, *, rotulo: str, casas: int,
             comparacao: pd.DataFrame | None = None, ano_comparacao: int | None = None) -> dict:
    """Pirâmide do core, com o outro ano em contorno por cima das barras.

    O contorno é o jeito clássico de comparar duas pirâmides: as barras são o
    ano escolhido, a linha é o outro, e o que sobra ou falta salta aos olhos.
    """
    opt = gc.piramide(atual, rotulo=rotulo)
    opt["tooltip"]["casas"] = casas
    if comparacao is None or comparacao.empty or "series" not in opt:
        return opt

    faixas = opt["yAxis"]["data"]
    nome = str(ano_comparacao)
    limite = float(opt["xAxis"]["max"])
    for sexo, sinal, texto in (("M", -1, "Homens"), ("F", 1, "Mulheres")):
        por_faixa = comparacao[comparacao["sexo"] == sexo].set_index("faixa_etaria")["valor"]
        dados = []
        for faixa in faixas:
            v = por_faixa.get(faixa)
            if v is None or pd.isna(v):
                dados.append({"name": faixa, "value": None})
                continue
            limite = max(limite, float(v))
            dados.append({
                "name": faixa, "value": sinal * float(v),
                "tooltip": f"<b>{escape(faixa)} · {texto}, {nome}</b><br/>"
                           f"{escape(rotulo)}: <b>{estilo.formatar(float(v), casas)}</b>",
            })
        opt["series"].append({
            "id": f"comparacao-{sexo}", "name": nome, "type": "bar", "stack": "comparacao",
            "data": dados, "barGap": "-100%", "z": 3,
            "itemStyle": {"color": "rgba(0,0,0,0)", "borderColor": COR_CONTORNO, "borderWidth": 1.4},
            "emphasis": {"disabled": True},
        })
    opt["legend"]["data"] = [*opt["legend"]["data"], nome]
    opt["xAxis"]["min"], opt["xAxis"]["max"] = -limite, limite
    return opt


def grupos_por_ano(serie: pd.DataFrame) -> dict:
    """Os três grandes grupos de idade, ano a ano, empilhados em 100%."""
    nomes = {m: ind.rotulo(m, curto=True) for m in ind.GRUPOS_IDADE}
    longo = serie.melt(id_vars="ano", value_vars=list(ind.GRUPOS_IDADE), var_name="metrica", value_name="pct")
    longo["categoria"] = longo["metrica"].map(nomes)
    opt = gc.composicao_por_ano(longo[["ano", "categoria", "pct"]], cor=ind.cor("pct_15_64"))
    if "series" not in opt:
        return opt
    # cada grupo com a sua cor (a mesma dos cards e do mapa), não um tom só
    por_nome = {nomes[m]: ind.cor(m) for m in ind.GRUPOS_IDADE}
    for s in opt["series"]:
        s["itemStyle"]["color"] = por_nome.get(s["name"], s["itemStyle"]["color"])
    opt["yAxis"]["name"] = "% da população"
    opt["xAxis"]["name"] = ""
    # o "100" do eixo não cabia na margem do core
    opt["grid"]["left"] = 64
    return opt


def dependencia_por_ano(serie: pd.DataFrame, ano: int) -> dict:
    """Razão de dependência total, de jovens e de idosos ao longo dos anos."""
    return gc.linhas_anuais(
        serie,
        series={
            "razao_dependencia": ("Total", ind.cor("razao_dependencia")),
            "dependencia_jovem": ("Jovens (0 a 14)", ind.cor("dependencia_jovem")),
            "dependencia_idosa": ("Idosos (65+)", ind.cor("dependencia_idosa")),
        },
        rotulo="Por 100 de 15 a 64", ano=ano, casas=1,
    )


def frase_bonus(serie: pd.DataFrame) -> str:
    """Onde o recorte está na janela do bônus demográfico, em uma frase."""
    base = serie.dropna(subset=["razao_dependencia"])
    if len(base) < 2:
        return ""
    primeiro, ultimo = base.iloc[0], base.iloc[-1]
    minimo = base.loc[base["razao_dependencia"].idxmin()]
    fmt = estilo.formatar
    if int(minimo["ano"]) == int(ultimo["ano"]):
        return (f"A dependência caiu de {fmt(primeiro['razao_dependencia'], 1)} para "
                f"{fmt(ultimo['razao_dependencia'], 1)} entre {int(primeiro['ano'])} e {int(ultimo['ano'])}: "
                "a janela do bônus demográfico ainda está aberta.")
    if int(minimo["ano"]) == int(primeiro["ano"]):
        return (f"A dependência só subiu desde {int(primeiro['ano'])} "
                f"({fmt(primeiro['razao_dependencia'], 1)} → {fmt(ultimo['razao_dependencia'], 1)}): "
                "a janela do bônus demográfico já tinha fechado.")
    return (f"A dependência chegou ao menor valor em {int(minimo['ano'])} "
            f"({fmt(minimo['razao_dependencia'], 1)}) e voltou a subir: a janela do bônus "
            "demográfico está se fechando, porque a subida dos idosos já compensa a queda dos jovens.")
