"""As contas de src/dados.py batem entre si e com o que se sabe do Brasil."""

from __future__ import annotations

import pytest

from src import dados

ANO = dados.anos()[-1]


def test_anos_vao_de_2010_a_2025() -> None:
    assert dados.anos() == list(range(2010, 2026))


def test_brasil_tem_populacao_e_indicadores_plausiveis() -> None:
    k = dados.kpis(ANO)
    assert 200e6 < k["populacao"] < 230e6
    assert 10 < k["pct_60"] < 25
    # há mais mulheres que homens no Brasil
    assert 90 < k["razao_sexo"] < 100
    assert 30 < k["idade_mediana"] < 40


def test_estados_somam_o_brasil() -> None:
    estados = dados.valores("populacao", ANO, "UF")
    assert len(estados) == 27
    assert estados.sum() == pytest.approx(dados.kpis(ANO)["populacao"])


def test_municipios_somam_o_estado() -> None:
    municipios = dados.valores("populacao", ANO, "MUN", "PE")
    assert municipios.sum() == pytest.approx(dados.kpis(ANO, "PE")["populacao"])


def test_piramide_fecha_com_a_populacao_e_termina_em_80_mais() -> None:
    p = dados.piramide(ANO, "RS")
    assert p["valor"].sum() == pytest.approx(dados.kpis(ANO, "RS")["populacao"])
    # o 80 do arquivo é "80 ou mais": não pode virar "80 a 84"
    assert p.sort_values("faixa_ord")["faixa_etaria"].iloc[-1] == "80+"
    assert "80 a 84" not in set(p["faixa_etaria"])


def test_piramide_em_proporcao_soma_100() -> None:
    assert dados.piramide(ANO, None, proporcao=True)["valor"].sum() == pytest.approx(100)


def test_municipio_tem_nome_e_uf() -> None:
    assert dados.nome("355030") == "São Paulo (SP)"
    assert dados.uf_de("355030") == "SP"
    assert dados.nome(None) == "Brasil"


def test_grandes_grupos_somam_100_e_dependencia_fecha() -> None:
    k = dados.kpis(ANO, "BA")
    assert k["pct_0_14"] + k["pct_15_64"] + k["pct_65"] == pytest.approx(100)
    assert k["dependencia_jovem"] + k["dependencia_idosa"] == pytest.approx(k["razao_dependencia"])


def test_crescimento_bate_com_a_populacao_e_nao_existe_no_primeiro_ano() -> None:
    atual, antes = dados.kpis(ANO)["populacao"], dados.kpis(ANO - 1)["populacao"]
    assert dados.kpis(ANO)["crescimento"] == pytest.approx((atual / antes - 1) * 100)
    assert dados.kpis(dados.anos()[0])["crescimento"] is None


def test_densidade_do_brasil_e_do_df_batem_com_o_ibge() -> None:
    # IBGE: ~8,51 milhões de km² no Brasil e ~5.760 km² no DF
    k = dados.kpis(ANO)
    assert k["populacao"] / k["densidade"] == pytest.approx(8.51e6, rel=0.01)
    df = dados.kpis(ANO, "DF")
    assert df["populacao"] / df["densidade"] == pytest.approx(5760, rel=0.02)


def test_serie_bate_com_os_cards_ano_a_ano() -> None:
    serie = dados.serie("PE").set_index("ano")
    for ano in (dados.anos()[1], ANO):
        k = dados.kpis(ano, "PE")
        for metrica in ("populacao", "crescimento", "densidade", "idade_mediana", "pct_65"):
            assert serie.loc[ano, metrica] == pytest.approx(k[metrica]), (ano, metrica)


def test_esperanca_de_vida_do_estado_e_a_do_ibge() -> None:
    # Projeções 2024, tab4: SC 2025 = 78,44 (homens 75,58, mulheres 81,26)
    k = dados.kpis(2025, "SC")
    assert k["esperanca_vida"] == pytest.approx(78.44, abs=0.01)
    assert k["esperanca_vida_h"] < k["esperanca_vida"] < k["esperanca_vida_m"]


def test_municipio_herda_a_esperanca_do_estado() -> None:
    assert dados.kpis(ANO, "355030")["esperanca_vida"] == dados.kpis(ANO, "SP")["esperanca_vida"]
    assert dados.esperanca_herdada("355030") and not dados.esperanca_herdada("SP")


def test_esperanca_do_brasil_fica_entre_os_estados() -> None:
    estados = dados.valores("esperanca_vida", ANO, "UF")
    brasil = dados.kpis(ANO)["esperanca_vida"]
    assert estados.min() < brasil < estados.max()
    assert dados.esperanca_estimada(None)


def test_covid_aparece_na_esperanca_de_vida() -> None:
    serie = dados.serie().set_index("ano")["esperanca_vida"]
    assert serie[2021] < serie[2019] - 2


sinasc = pytest.mark.skipif(not dados.tem_nascimentos(), reason="data/nascimentos.parquet ausente")


@sinasc
@pytest.mark.parametrize(("ano", "total"), [(2010, 2_861_868), (2015, 3_017_668), (2020, 2_730_145)])
def test_nascidos_vivos_batem_com_o_sinasc(ano: int, total: int) -> None:
    # totais publicados pelo DATASUS (TabNet, nascidos vivos por residência)
    assert dados.kpis(ano)["nascidos"] == total


@sinasc
def test_fecundidade_do_brasil_e_plausivel_e_cai() -> None:
    serie = dados.serie().set_index("ano")["fecundidade"].dropna()
    assert serie.between(1.4, 2.0).all(), serie
    assert serie.iloc[-1] < serie.loc[2015]


@sinasc
def test_estados_somam_os_nascimentos_do_brasil() -> None:
    ano = dados.anos_nascimentos()[-1]
    estados = dados.valores("nascidos", ano, "UF").sum()
    # a diferença são as mães com município de residência ignorado e sem UF
    assert estados == pytest.approx(dados.kpis(ano)["nascidos"], rel=0.001)


@sinasc
def test_natalidade_e_nascidos_sobre_populacao() -> None:
    ano = dados.anos_nascimentos()[-1]
    k = dados.kpis(ano, "AM")
    assert k["natalidade"] == pytest.approx(k["nascidos"] / k["populacao"] * 1000)
    assert 0 < k["pct_maes_adolescentes"] < 30
    assert 20 < k["idade_media_mae"] < 35


@sinasc
def test_ano_sem_sinasc_fica_vazio_e_nao_zero() -> None:
    k = dados.kpis(dados.anos()[-1])
    if dados.anos()[-1] not in dados.anos_nascimentos():
        assert k["nascidos"] is None and k["fecundidade"] is None


def test_ranking_vem_do_maior_para_o_menor() -> None:
    r = dados.ranking("pct_60", ANO, "UF")
    assert r["valor"].is_monotonic_decreasing
    assert r["chave"].iloc[0] == "RS"
