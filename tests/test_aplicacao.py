"""O app inteiro rodando no AppTest.

Confere também que não tem aviso: o resiliencia.painel esconde erro de bloco
atrás de um aviso, e o app "sobe" mesmo com gráfico quebrado.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import indicadores

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _rodar(**estado) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=120)
    for chave, valor in estado.items():
        at.session_state[chave] = valor
    return at.run()


def _conferir(at: AppTest) -> None:
    assert not at.exception, [e.value for e in at.exception]
    assert not at.warning, [w.value for w in at.warning]


def _componentes(at: AppTest, trecho: str) -> list[dict]:
    return [json.loads(c.proto.json_args) for c in at.get("component_instance")
            if trecho in c.proto.json_args]


def test_sobe_com_mapa_cards_e_graficos() -> None:
    at = _rodar()
    _conferir(at)
    assert len(_componentes(at, '"spec"')) == 1, "o mapa não foi desenhado"
    # pirâmide, grupos, dependência, duas séries e o ranking
    assert len(_componentes(at, '"option"')) == 6
    assert sum(m.value.startswith('<div class="kpi-card"') for m in at.markdown) == len(indicadores.LAYOUT_KPI)


@pytest.mark.parametrize("selecionado", ["MG", "355030"])
def test_recorte_muda_os_numeros(selecionado: str) -> None:
    """Simula o clique pondo `selecionado` direto (o AppTest não clica no mapa)."""
    geral, recorte = _rodar(), _rodar(selecionado=selecionado)
    _conferir(recorte)
    cards = lambda at: [m.value for m in at.markdown if m.value.startswith('<div class="kpi-card"')]  # noqa: E731
    assert cards(geral) != cards(recorte)


def test_esperanca_com_municipio_aberto_fica_nos_estados() -> None:
    at = _rodar(metrica="esperanca_vida", selecionado="355030")
    _conferir(at)
    # o spec do deck vem como texto JSON dentro do JSON do componente
    spec = _componentes(at, '"spec"')[0]["spec"]
    # o mapa desenha os 27 estados, não os municípios de SP
    assert '"SP"' in spec and '"355030"' not in spec
    assert any("valor de SP" in m.value for m in at.markdown)


def test_tema_leva_a_primeira_metrica_dele() -> None:
    at = _rodar(tema="nascimentos")
    _conferir(at)
    assert at.session_state["metrica"] == "fecundidade"


@pytest.mark.parametrize("metrica", indicadores.METRICAS_MAPA)
def test_todas_as_metricas_do_mapa_desenham(metrica: str) -> None:
    _conferir(_rodar(metrica=metrica, visao_mapa="MUN"))
