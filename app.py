"""Painel Demográfico do Brasil. Aqui só monta a tela; as contas ficam em src/."""

from __future__ import annotations

import streamlit as st
from cenarios_core import grafico_componente, mapa, mapa_componente, resiliencia

from src import dados, estilo, graficos
from src import indicadores as ind

TERRITORIO = "Brasil"

st.set_page_config(page_title="Painel Demográfico do Brasil", layout="wide")
st.markdown(estilo.css(), unsafe_allow_html=True)

# Brasil é quase quadrado, então o mapa é alto.
ALTURA_MAPA = 540
TOPO_RANKING = 10
# Quintis primeiro: com 5.571 municípios, densidade e crescimento têm pontas
# tão longas que as quebras naturais deixam quase tudo numa cor só.
CLASSIFICACOES = {"QUARTIL": "Quintis", "NATURAL": "Quebras naturais"}
NIVEIS = {"UF": "Estados", "MUN": "Municípios"}


# ---------------------------------------------------------------------------
# Dados (com cache)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _geometrias_ufs():
    return mapa.geometrias_geojson(dados.ufs())


@st.cache_resource(show_spinner=False)
def _geometrias_brasil():
    # a malha não muda, só a cor
    return mapa.geometrias_geojson(dados.territorio())


@st.cache_resource(show_spinner=False)
def _geometrias_da_uf(uf: str):
    return mapa.geometrias_geojson(dados.municipios_da_uf(uf))


@st.cache_data(show_spinner=False)
def _kpis(ano: int, recorte: str | None):
    return dados.kpis(ano, recorte)


@st.cache_data(show_spinner=False)
def _valores(metrica: str, ano: int, nivel: str, uf: str | None = None):
    return dados.valores(metrica, ano, nivel, uf)


@st.cache_data(show_spinner=False)
def _serie(recorte: str | None):
    return dados.serie(recorte)


@st.cache_data(show_spinner=False)
def _piramide(ano: int, recorte: str | None, proporcao: bool):
    return dados.piramide(ano, recorte, proporcao)


@st.cache_data(show_spinner=False)
def _ranking(metrica: str, ano: int, nivel: str, uf: str | None):
    return dados.ranking(metrica, ano, nivel, uf)


# ---------------------------------------------------------------------------
# Recorte selecionado e cliques
# ---------------------------------------------------------------------------

anos = dados.anos()
if "selecionado" not in st.session_state:
    st.session_state.selecionado = None

# o seletor vem depois, mas o valor já está no estado
por_estado = st.session_state.get("visao_mapa", "UF") == "UF"


def _clicar(alvo: str) -> None:
    """Clicar de novo no selecionado volta um nível."""
    atual = st.session_state.selecionado
    if alvo != atual:
        st.session_state.selecionado = alvo
    else:
        st.session_state.selecionado = dados.uf_de(atual) if por_estado and not dados.eh_uf(atual) else None


# Lê os cliques antes de desenhar.
for _comp, _nonce, _ler in (
    ("mapa", "clique_mapa", mapa_componente.alvo_do_clique),
    ("ranking", "clique_ranking", grafico_componente.alvo_do_clique),
):
    _alvo, _novo = _ler(st.session_state.get(_comp), st.session_state.get(_nonce))
    if _novo:
        st.session_state[_nonce] = _novo
    if _alvo:
        _clicar(str(_alvo))

selecionado = st.session_state.selecionado
local = dados.nome(selecionado, TERRITORIO)
# a UF cujos municípios o mapa está mostrando
uf_aberta = dados.uf_de(selecionado) if por_estado else None

ano = st.session_state.get("ano")
ano = ano if ano in anos else anos[-1]
serie_local = _serie(selecionado)


# ---------------------------------------------------------------------------
# Cabeçalho e cards
# ---------------------------------------------------------------------------

st.markdown(estilo.cabecalho("Painel Demográfico do Brasil", f"{local} • {ano}"), unsafe_allow_html=True)

atuais = _kpis(ano, selecionado)
anteriores = _kpis(ano - 1, selecionado) if ano - 1 in anos else {}
with st.container(key="faixa-kpis"):
    for coluna, m in zip(st.columns(len(ind.LAYOUT_KPI)), ind.LAYOUT_KPI, strict=True):
        with coluna, resiliencia.painel(ind.rotulo(m, curto=True)):
            valor = atuais.get(m)
            ano_card, anterior = ano, anteriores.get(m)
            ultimo_sinasc = (dados.anos_nascimentos() or [None])[-1]
            if m in ind.NASCIMENTOS and valor is None and ultimo_sinasc and ano > ultimo_sinasc:
                # o SINASC fecha depois da população: o card mostra o último ano fechado
                ano_card = ultimo_sinasc
                valor = _kpis(ano_card, selecionado).get(m)
                anterior = _kpis(ano_card - 1, selecionado).get(m)
            texto = estilo.formatar(valor, ind.casas(m)) + (ind.sufixo(m) if valor is not None else "")
            if m == "crescimento" and valor is not None and valor > 0:
                texto = "+" + texto
            if valor is not None and ano_card != ano:
                subtitulo = f"{local} • {ano_card} (SINASC)"
            elif valor is not None:
                subtitulo = f"{local} • {ano}"
            elif m in ind.NASCIMENTOS:
                anos_sinasc_card = dados.anos_nascimentos()
                subtitulo = f"SINASC vai até {anos_sinasc_card[-1]}" if anos_sinasc_card else "sem o SINASC"
            else:
                subtitulo = f"sem o ano anterior a {ano}"
            if m == "esperanca_vida" and valor is not None:
                # o IBGE publica por estado: deixar claro quando não é o número do próprio recorte
                if dados.esperanca_estimada(selecionado):
                    subtitulo = f"média dos estados • {ano}"
                elif dados.esperanca_herdada(selecionado):
                    subtitulo = f"valor de {dados.uf_de(selecionado)} • {ano}"
            st.markdown(estilo.card(
                ind.rotulo(m), texto, ind.cor(m),
                subtitulo=subtitulo,
                variacao_html=estilo.variacao(valor, anterior, casas=ind.casas(m),
                                              ano_anterior=ano_card - 1, relativa=m == "populacao",
                                              sufixo=ind.sufixo(m)),
                icone=ind.icone(m), ajuda=ind.ajuda(m),
            ), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------

def _trocar_tema() -> None:
    """Trocou o tema: a métrica vai para a primeira dele."""
    tema_novo = st.session_state.get("tema") or "estrutura"
    st.session_state["metrica"] = ind.TEMAS[tema_novo][1][0]


# quem chega com uma métrica (link, teste) cai no tema dela
if st.session_state.get("metrica") in ind.METRICAS_MAPA and "tema" not in st.session_state:
    st.session_state["tema"] = next(t for t, (_, ms) in ind.TEMAS.items() if st.session_state["metrica"] in ms)

with st.container(border=True, key="cartao-controles"):
    col_ano, col_tema, col_metrica, col_nivel, col_cores = st.columns([1, 2.6, 4, 1.6, 1.8],
                                                                      vertical_alignment="top")
    col_ano.selectbox("Ano", anos[::-1], key="ano")
    tema = col_tema.segmented_control(
        "Tema", list(ind.TEMAS), format_func=lambda t: ind.TEMAS[t][0], default="estrutura", key="tema",
        on_change=_trocar_tema,
    ) or "estrutura"
    metricas_tema = ind.TEMAS[tema][1]
    if st.session_state.get("metrica") not in metricas_tema:
        st.session_state["metrica"] = metricas_tema[0]
    metrica = col_metrica.segmented_control(
        "Métrica do mapa", metricas_tema, format_func=lambda m: ind.rotulo(m, curto=True),
        key="metrica",
    ) or metricas_tema[0]
    col_nivel.segmented_control("Nível do mapa", list(NIVEIS), format_func=NIVEIS.get, default="UF",
                                key="visao_mapa", on_change=lambda: st.session_state.update(selecionado=None),
                                disabled=ind.so_estados(metrica),
                                help="Esta métrica só existe por estado." if ind.so_estados(metrica) else None)
    regua = ind.regua(metrica)
    if regua:
        # crescimento (o zero) e fecundidade (a reposição, 2,1) têm régua própria:
        # o ponto que dá sentido ao número não pode mudar de lugar entre anos
        col_cores.caption("Cores: régua fixa, igual em todo ano.")
        classificacao = "FIXA"
    else:
        classificacao = col_cores.segmented_control(
            "Cores", list(CLASSIFICACOES), format_func=CLASSIFICACOES.get, default="QUARTIL",
            key="classificacao",
        ) or "QUARTIL"

# métrica que só existe por estado (esperança de vida): o mapa fica nos 27
if ind.so_estados(metrica):
    uf_aberta = None
# só os 27 estados quando nenhum está aberto
estados = ind.so_estados(metrica) or (por_estado and uf_aberta is None)
casas, rotulo, rotulo_curto = ind.casas(metrica), ind.rotulo(metrica), ind.rotulo(metrica, curto=True)
onde = f" em {dados.nome_uf(uf_aberta)}" if uf_aberta else ""
regua_mapa = {"cortes_fixos": regua["cortes"], "nomes_fixos": regua["nomes"], "casas_regua": 1} if regua else {}
anos_sinasc = dados.anos_nascimentos()
# O SINASC fecha depois da população: num ano que ele ainda não tem, o mapa e
# o ranking de nascimentos vão para o último ano fechado (e o título diz qual).
ano_m = anos_sinasc[-1] if metrica in ind.NASCIMENTOS and anos_sinasc and ano > anos_sinasc[-1] else ano
sem_sinasc_no_ano = metrica in ind.NASCIMENTOS and ano_m not in anos_sinasc

if estados:
    valores = _valores(metrica, ano_m, "UF")
    populacao = _valores("populacao", ano, "UF")
else:
    valores = _valores(metrica, ano_m, "MUN", uf_aberta)
    populacao = _valores("populacao", ano, "MUN", uf_aberta)
escala = mapa.escala(valores, ind.rampa(metrica), metodo=classificacao, decimais=casas, **regua_mapa)


# ---------------------------------------------------------------------------
# Mapa
# ---------------------------------------------------------------------------

col_mapa, col_graficos = st.columns([1.05, 1], gap="medium")

with col_mapa, resiliencia.painel("Mapa"), st.container(border=True, key="cartao-mapa"):
    st.markdown(estilo.titulo_bloco(f"Mapa — {rotulo}{onde}, {ano_m}", ajuda=ind.ajuda(metrica)),
                unsafe_allow_html=True)
    if estados:
        camada, chave, nome, geometrias, divisas = dados.ufs(), "uf", "nome_uf", _geometrias_ufs(), None
    elif uf_aberta:
        camada, chave, nome = dados.municipios_da_uf(uf_aberta), "cod_mun6", "nome_mun"
        geometrias, divisas = _geometrias_da_uf(uf_aberta), None
    else:
        camada, chave, nome = dados.territorio(), "cod_mun6", "nome_mun"
        geometrias, divisas = _geometrias_brasil(), _geometrias_ufs()
    desenho, escala_mapa = mapa.deck(
        camada, valores, chave=chave, coluna_nome=nome, rampa=ind.rampa(metrica),
        rotulo_metrica=rotulo, decimais=casas, altura=ALTURA_MAPA, geometrias=geometrias,
        destacado=None if dados.eh_uf(selecionado) or estados else selecionado, metodo=classificacao,
        detalhes=[("População", populacao, ind.cor("populacao"), 0)],
        divisas=divisas, quadro_ilhas=False, **regua_mapa,
    )
    mapa_componente.desenhar(desenho, altura=ALTURA_MAPA, key="mapa", titulo=f"Mapa do Brasil: {rotulo}")
    contagem = mapa.classificar(valores.reindex(camada[chave]), escala_mapa).value_counts()
    st.markdown(mapa.legenda(escala_mapa, rotulo_curto, contagem=contagem,
                             nomes=regua["nomes"] if regua else None), unsafe_allow_html=True)
    if ind.so_estados(metrica):
        st.caption("O IBGE publica a esperança de vida por estado, não por município. "
                   "Projeções da População, revisão 2024.")
    if ano_m != ano:
        st.caption(f"O SINASC vai de {anos_sinasc[0]} a {anos_sinasc[-1]}: {ano} ainda não foi fechado "
                   f"pelo DATASUS, então o mapa mostra {ano_m}.")
    elif sem_sinasc_no_ano:
        st.caption(f"O SINASC não tem {ano}.")
    elif metrica in ind.NASCIMENTOS and not estados:
        st.caption("Em município pequeno, poucos nascimentos a mais ou a menos mudam muito a taxa: "
                   "compare com os anos vizinhos.")
    if metrica == "crescimento" and ano == anos[0]:
        st.caption(f"{anos[0]} é o primeiro ano da base: não há ano anterior para medir o crescimento.")
    if uf_aberta and not dados.eh_uf(selecionado):
        st.button(f"Ver {dados.nome_uf(uf_aberta)} inteiro",
                  on_click=lambda: st.session_state.update(selecionado=uf_aberta))
    if selecionado:
        st.button(f"Ver {TERRITORIO} inteiro", on_click=lambda: st.session_state.update(selecionado=None))
    elif estados:
        st.caption("Clique num estado para abrir os municípios dele.")
    else:
        st.caption("Clique num município para ver os números dele.")


# ---------------------------------------------------------------------------
# Gráficos ao lado do mapa
# ---------------------------------------------------------------------------

with col_graficos, st.container(border=True, key="cartao-graficos"):
    aba_piramide, aba_grupos, aba_evolucao, aba_ranking = st.tabs(
        ["Pirâmide etária", "Grupos de idade", "Evolução temporal",
         "Ranking de estados" if estados else "Ranking de municípios"])

    with aba_piramide, resiliencia.painel("Pirâmide etária"):
        st.markdown(estilo.titulo_bloco(f"Pirâmide etária — {local}, {ano}"), unsafe_allow_html=True)
        col_cmp, col_pct = st.columns([1.2, 1], vertical_alignment="bottom")
        outros = [a for a in anos if a != ano]
        ano_cmp = col_cmp.selectbox("Comparar com", [None, *outros], index=1 if outros else 0,
                                    format_func=lambda a: "nenhum ano" if a is None else str(a),
                                    key="ano_comparacao")
        proporcao = col_pct.toggle("Em % da população", value=False, key="piramide_pct",
                                   help="Deixa comparar a forma da pirâmide entre lugares e anos.")
        grafico_componente.desenhar(
            graficos.piramide(
                _piramide(ano, selecionado, proporcao), rotulo="% da população" if proporcao else "Pessoas",
                casas=2 if proporcao else 0,
                comparacao=_piramide(ano_cmp, selecionado, proporcao) if ano_cmp else None,
                ano_comparacao=ano_cmp,
            ),
            altura=ALTURA_MAPA - 110, key="piramide",
        )
        st.caption("Faixas de 5 anos; a última junta todo mundo com 80 anos ou mais."
                   + (f" Barras: {ano}. Contorno: {ano_cmp}." if ano_cmp else ""))

    with aba_grupos, resiliencia.painel("Grupos de idade"):
        st.markdown(estilo.titulo_bloco(f"Crianças, idade de trabalhar e idosos — {local}"),
                    unsafe_allow_html=True)
        grafico_componente.desenhar(graficos.grupos_por_ano(serie_local), altura=250, key="grupos")
        st.markdown(estilo.titulo_bloco(
            f"Razão de dependência — {local}",
            ajuda="Quantas pessoas fora da idade de trabalhar há para cada 100 de 15 a 64 anos, "
                  "separando crianças e idosos."), unsafe_allow_html=True)
        grafico_componente.desenhar(graficos.dependencia_por_ano(serie_local, ano), altura=250, key="dependencia")
        st.caption(graficos.frase_bonus(serie_local))

    with aba_evolucao, resiliencia.painel("Evolução"):
        st.markdown(estilo.titulo_bloco(f"{rotulo} por ano — {local}"), unsafe_allow_html=True)
        if metrica == "esperanca_vida":
            # homens e mulheres juntos: a diferença entre os dois é parte da história
            grafico = grafico_componente.linhas_anuais(
                serie_local, series={c: (ind.rotulo(c, curto=True) if c != metrica else "Total", ind.cor(c))
                                     for c in ("esperanca_vida", "esperanca_vida_h", "esperanca_vida_m")},
                rotulo="Anos", ano=ano, casas=1,
            )
            # o eixo a partir do zero achatava tudo entre 70 e 82
            base = serie_local[["esperanca_vida_h", "esperanca_vida_m"]]
            if base.notna().any().any():
                grafico["yAxis"]["min"] = int(base.min().min()) - 2
                grafico["yAxis"]["max"] = int(base.max().max()) + 2
        elif metrica == "fecundidade":
            # a linha da reposição é o que dá sentido ao número
            grafico = grafico_componente.linhas_anuais(
                serie_local.dropna(subset=["fecundidade"]), series={"fecundidade": ("Fecundidade", ind.cor(metrica))},
                rotulo="Filhos por mulher", ano=ano, casas=2, referencias=[("Reposição: 2,1", 2.1)],
            )
        else:
            base = serie_local[["ano", metrica]].rename(columns={metrica: "valor"})
            if metrica in ind.NASCIMENTOS:
                base = base.dropna()
            grafico = grafico_componente.evolucao_anual(base, rotulo=rotulo_curto, cor=ind.cor(metrica), ano=ano)
        grafico_componente.desenhar(grafico, altura=240, key="anual")
        if metrica == "esperanca_vida" and dados.esperanca_estimada(selecionado):
            st.caption("Brasil: média dos estados ponderada pela população, uma aproximação do "
                       "número nacional do IBGE.")
        # embaixo, a contagem que dá base à taxa: nascidos no tema Nascimentos, população no resto
        contagem = "nascidos" if metrica in ind.NASCIMENTOS else "populacao"
        pop = serie_local[["ano", contagem]].rename(columns={contagem: "valor"}).dropna()
        # o eixo não cabe "213.000.000": vai em milhões ou em mil, conforme o lugar
        maior = pop["valor"].max() if not pop.empty else 0
        divisor, unidade = (1e6, "milhões") if maior >= 1e6 else (1e3, "mil") if maior >= 1e4 else (1, "")
        nome_contagem = ind.rotulo(contagem)
        sufixo_unidade = f" ({unidade})" if unidade else ""
        st.markdown(estilo.titulo_bloco(f"{nome_contagem} por ano{sufixo_unidade} — {local}"),
                    unsafe_allow_html=True)
        grafico_componente.desenhar(
            grafico_componente.evolucao_anual(pop.assign(valor=pop["valor"] / divisor),
                                              rotulo=f"{nome_contagem}{sufixo_unidade}", cor=ind.cor(contagem),
                                              ano=ano),
            altura=220, key="anual-pop",
        )

    with aba_ranking, resiliencia.painel("Ranking"):
        brasil = _kpis(ano_m, None).get(metrica)
        referencia = ((f"Brasil: {estilo.formatar(brasil, casas)}{ind.sufixo(metrica)}", brasil)
                      if brasil is not None else None)
        if estados:
            st.markdown(estilo.titulo_bloco(f"{rotulo_curto} nos estados, {ano_m}"), unsafe_allow_html=True)
            tabela, altura_barra = _ranking(metrica, ano_m, "UF", None), 22
        else:
            st.markdown(estilo.titulo_bloco(
                f"{TOPO_RANKING} municípios com maior {rotulo_curto.lower()}{onde}, {ano_m}"), unsafe_allow_html=True)
            tabela, altura_barra = _ranking(metrica, ano_m, "MUN", uf_aberta).head(TOPO_RANKING), 34
        grafico_componente.desenhar(
            grafico_componente.ranking(
                tabela, rotulo=rotulo_curto, cor=ind.cor(metrica), escala=escala,
                selecionado=None if dados.eh_uf(selecionado) else selecionado, casas=casas,
                largura_rotulo=170, rotulos_valor=True, sufixo=ind.sufixo(metrica), referencia=referencia,
            ),
            altura=max(grafico_componente.ALTURA_MIN_RANKING, altura_barra * len(tabela) + 24),
            key="ranking",
        )
        st.caption("Linha tracejada: o Brasil. A cor da barra é a faixa do mapa."
                   + ("" if estados else " Município pequeno sobe fácil no ranking: confira a população."))


# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------

st.markdown(estilo.rodape(
    f"Fonte: IBGE, população por município, sexo e idade · {anos[0]} a {anos[-1]} · "
    "esperança de vida: IBGE, Projeções da População 2024 · nascimentos: SINASC/DATASUS"
    + (f", {dados.anos_nascimentos()[0]} a {dados.anos_nascimentos()[-1]}" if dados.anos_nascimentos() else "")
    + " · área calculada da malha municipal do IBGE"), unsafe_allow_html=True)
