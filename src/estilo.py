"""A cara do painel, com as peças de src/theme/ (as mesmas dos painéis de TB e hanseníase).

Aqui só tem o que é deste painel: a variação sem juízo de valor e o rodapé.
"""

from __future__ import annotations

from html import escape

from cenarios_core import formato

from src.theme import componentes as ui

AZUL = "#1E73BE"


def css() -> str:
    return ui.css_base() + ui.css_layout() + """
<style>
/* demografia não tem "bom" nem "ruim": a variação fica neutra */
.kpi-delta.kpi-neutro { opacity: .78; font-weight: 700; }
.rodape {
  border-top: 1px solid color-mix(in srgb, currentColor 14%, transparent);
  margin-top: 28px; padding: 10px 4px; font-size: 12px; opacity: .72;
  display: flex; justify-content: space-between; gap: 14px; flex-wrap: wrap;
}
</style>
"""


def formatar(valor: float | None, casas: int) -> str:
    if valor is None:
        return "—"
    return formato.formatar_inteiro(valor) if casas == 0 else formato.formatar_decimal(valor, casas)


def cabecalho(titulo: str, subtitulo: str) -> str:
    return ui.faixa_intro(titulo, escopo=subtitulo, cor=AZUL)


def variacao(atual: float | None, anterior: float | None, *, casas: int, ano_anterior: int,
             relativa: bool = False, sufixo: str = "") -> str:
    """Quanto mudou desde o ano anterior, sem verde nem vermelho.

    ``relativa`` dá a mudança em % (para a população). Nas proporções a
    diferença vai em pontos percentuais, que é o que se compara.
    """
    if atual is None or anterior is None:
        return ""
    diferenca = (atual / anterior - 1) * 100 if relativa and anterior else atual - anterior
    # "igual" é o que some no arredondamento do card
    if abs(diferenca) < 0.5 * 10 ** -(1 if relativa else casas):
        return f'<div class="kpi-delta kpi-neutro">≈ igual a {ano_anterior}</div>'
    seta = "↑" if diferenca > 0 else "↓"
    if relativa:
        texto = f"{formatar(abs(diferenca), 1)}%"
    elif sufixo == "%":
        texto = f"{formatar(abs(diferenca), casas)} p.p."
    else:
        texto = formatar(abs(diferenca), casas)
    return f'<div class="kpi-delta kpi-neutro">{seta} {texto} vs {ano_anterior}</div>'


def card(rotulo: str, valor: str, cor: str, *, subtitulo: str, variacao_html: str,
         icone: str, ajuda: str) -> str:
    return ui.kpi_card(rotulo, valor, cor=cor, subtitulo=subtitulo, badge_delta=variacao_html,
                       icone=icone, ajuda=ajuda)


def titulo_bloco(texto: str, ajuda: str = "") -> str:
    return ui.titulo_painel(texto, ajuda=ajuda)


def rodape(fonte: str) -> str:
    return (f'<div class="rodape"><span>{escape(fonte)}</span>'
            f'<span>Projeto Cenários+ · UnB</span></div>')
