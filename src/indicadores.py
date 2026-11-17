"""Os indicadores do painel: rótulo, cor, casas decimais e como ler.

As contas ficam em src/dados.py; aqui só o que a tela precisa saber de cada um.
"""

from __future__ import annotations

from cenarios_core import cores

METRICAS = {
    "populacao": {
        "rotulo": "População", "curto": "População", "cor": "#1E73BE", "casas": 0,
        "ajuda": "Total de habitantes no ano.",
        # contagem não vai pro mapa: pinta o tamanho do lugar, não a estrutura
    },
    "crescimento": {
        "rotulo": "Crescimento anual (%)", "curto": "Crescimento", "cor": "#2563EB", "casas": 2,
        "sufixo": "%",
        "ajuda": "Quanto a população mudou desde o ano anterior. Negativo: o lugar perdeu gente.",
        # Encolher e crescer são coisas diferentes: cor divergente e régua fixa,
        # igual em todo ano (o 0 fica sempre no mesmo lugar).
        "regua": {
            "cortes": [-100, -1, 0, 0.5, 1],
            "nomes": ("encolhe mais de 1%", "encolhe", "cresce pouco", "cresce", "cresce mais de 1%"),
            "rampa": ["#B42318", "#F4A582", "#D1E5F0", "#6BAED6", "#08519C"],
        },
    },
    "densidade": {
        "rotulo": "Densidade (hab./km²)", "curto": "Densidade", "cor": "#7C3AED", "casas": 1,
        "ajuda": "Habitantes por km². A área é a do contorno oficial do município.",
    },
    "pct_0_14": {
        "rotulo": "Crianças de 0 a 14 anos (%)", "curto": "0–14 anos", "cor": "#0E9F6E", "casas": 1,
        "sufixo": "%",
        "ajuda": "Quantas pessoas, em cada 100, têm de 0 a 14 anos.",
    },
    "pct_15_64": {
        "rotulo": "De 15 a 64 anos (%)", "curto": "15–64 anos", "cor": "#1E73BE", "casas": 1,
        "sufixo": "%",
        "ajuda": "A idade de trabalhar: quantas pessoas, em cada 100, têm de 15 a 64 anos.",
    },
    "pct_65": {
        "rotulo": "Idosos de 65 anos ou mais (%)", "curto": "65+ anos", "cor": "#B45309", "casas": 1,
        "sufixo": "%",
        "ajuda": "Quantas pessoas, em cada 100, têm 65 anos ou mais.",
    },
    "razao_dependencia": {
        "rotulo": "Razão de dependência", "curto": "Dependência", "cor": "#0F766E", "casas": 1,
        "ajuda": "Crianças (0 a 14) e idosos (65 ou mais) para cada 100 pessoas de 15 a 64 anos.",
    },
    "dependencia_jovem": {
        "rotulo": "Dependência de jovens", "curto": "Jovens", "cor": "#0E9F6E", "casas": 1,
        "ajuda": "Crianças (0 a 14) para cada 100 pessoas de 15 a 64 anos.",
    },
    "dependencia_idosa": {
        "rotulo": "Dependência de idosos", "curto": "Idosos", "cor": "#B45309", "casas": 1,
        "ajuda": "Idosos (65 ou mais) para cada 100 pessoas de 15 a 64 anos.",
    },
    "razao_sexo": {
        "rotulo": "Razão de sexo", "curto": "Razão de sexo", "cor": "#1D4ED8", "casas": 1,
        "ajuda": "Homens para cada 100 mulheres. Abaixo de 100, há mais mulheres.",
    },
    "idade_mediana": {
        "rotulo": "Idade mediana (anos)", "curto": "Idade mediana", "cor": "#BE185D", "casas": 1,
        "ajuda": "Metade da população tem menos que esta idade, e metade tem mais.",
    },
    "esperanca_vida": {
        "rotulo": "Esperança de vida ao nascer (anos)", "curto": "Esperança de vida", "cor": "#16A34A",
        "casas": 1,
        "ajuda": "Quantos anos, em média, viveria quem nasce neste ano, se as taxas de mortalidade do "
                 "ano se mantivessem. IBGE, Projeções da População (revisão 2024), por estado.",
        # o IBGE só publica por estado: o mapa não desce a município
        "so_estados": True,
    },
    "esperanca_vida_h": {"rotulo": "Homens", "curto": "Homens", "cor": "#1D4ED8", "casas": 1, "ajuda": ""},
    "esperanca_vida_m": {"rotulo": "Mulheres", "curto": "Mulheres", "cor": "#BE185D", "casas": 1, "ajuda": ""},
    # --- Nascimentos (SINASC) ---
    "nascidos": {
        "rotulo": "Nascidos vivos", "curto": "Nascidos vivos", "cor": "#DB2777", "casas": 0,
        "ajuda": "Nascidos vivos de mães que moram no lugar. SINASC/DATASUS.",
    },
    "fecundidade": {
        "rotulo": "Fecundidade (filhos por mulher)", "curto": "Fecundidade", "cor": "#DB2777",
        "casas": 2,
        "ajuda": "Quantos filhos, em média, uma mulher teria na vida com as taxas do ano. "
                 "Abaixo de 2,1 a população não se repõe sozinha (sem migração).",
        # A reposição (2,1) fica sempre no mesmo lugar da régua.
        "regua": {
            "cortes": [0, 1.5, 1.8, 2.1, 2.5],
            "nomes": ("muito baixa", "baixa", "abaixo da reposição", "acima da reposição", "alta"),
        },
    },
    "natalidade": {
        "rotulo": "Taxa de natalidade (por mil hab.)", "curto": "Natalidade", "cor": "#9D174D", "casas": 1,
        "ajuda": "Nascidos vivos no ano para cada mil habitantes.",
    },
    "pct_maes_adolescentes": {
        "rotulo": "Mães adolescentes (%)", "curto": "Mães adolescentes", "cor": "#C2410C", "casas": 1,
        "sufixo": "%",
        "ajuda": "Nascimentos de mães com menos de 20 anos, em cada 100 nascimentos (com idade informada).",
    },
    "idade_media_mae": {
        "rotulo": "Idade média da mãe (anos)", "curto": "Idade da mãe", "cor": "#7E22CE", "casas": 1,
        "ajuda": "Idade média das mães no nascimento do filho.",
    },
}

# O envelhecimento em detalhe (60+, índice de envelhecimento) é do painel
# irmão, o de Envelhecimento. Aqui é a população inteira. A razão de sexo e a
# dependência saíram dos cards (continuam no mapa, e a dependência tem a aba
# de grupos de idade).
LAYOUT_KPI = ("populacao", "crescimento", "fecundidade", "esperanca_vida", "idade_mediana", "densidade")

# O mapa escolhe primeiro o tema, depois a métrica: tudo numa linha não cabia.
TEMAS = {
    "estrutura": ("Estrutura", ("pct_0_14", "pct_65", "razao_dependencia", "idade_mediana", "razao_sexo")),
    "crescimento": ("Crescimento", ("crescimento", "densidade")),
    "nascimentos": ("Nascimentos", ("fecundidade", "natalidade", "pct_maes_adolescentes", "idade_media_mae")),
    "mortalidade": ("Mortalidade", ("esperanca_vida",)),
}

METRICAS_MAPA = tuple(m for _, metricas in TEMAS.values() for m in metricas)

# métricas que vêm do SINASC (o último ano é o do SINASC, não o da população)
NASCIMENTOS = ("nascidos", "fecundidade", "natalidade", "pct_maes_adolescentes", "idade_media_mae")

# os três grandes grupos de idade, na ordem da vida
GRUPOS_IDADE = ("pct_0_14", "pct_15_64", "pct_65")

# miolo de SVG 24x24, no traço dos ícones dos outros painéis
ICONES = {
    # duas pessoas
    "populacao": '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/>'
                 '<circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2A5 5 0 0 1 21 19"/>',
    # linha subindo
    "crescimento": '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
    # quadrado cheio de pontos: gente por área
    "densidade": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1"/>'
                 '<circle cx="16" cy="8" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="8" cy="16" r="1"/>'
                 '<circle cx="16" cy="16" r="1"/>',
    # mão segurando: quem depende de quem
    "razao_dependencia": '<path d="M3 14h4l5 3 8-4"/><path d="M7 14l3-3h4"/><circle cx="15" cy="6" r="2.5"/>',
    # os dois símbolos de sexo
    "razao_sexo": '<circle cx="9" cy="10" r="4"/><path d="M9 14v7M6.5 18.5h5"/>'
                  '<circle cx="16" cy="8" r="3"/><path d="M18.2 5.8L21 3M18 3h3v3"/>',
    # carrinho de bebê
    "fecundidade": '<path d="M4 10h12a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"/><path d="M16 10V5a6 6 0 0 0-6 5"/>'
                   '<circle cx="7" cy="18" r="2"/><circle cx="14" cy="18" r="2"/>',
    # coração com batimento
    "esperanca_vida": '<path d="M12 20s-7-4.4-9-9a4.8 4.8 0 0 1 9-3 4.8 4.8 0 0 1 9 3c-.4 1-1 2-1.7 3"/>'
                      '<path d="M3 13h5l2-3 3 6 2-3h6"/>',
    # régua com o meio marcado
    "idade_mediana": '<path d="M3 17h18"/><path d="M5 17v-3M9 17v-3M15 17v-3M19 17v-3"/>'
                     '<path d="M12 17V7"/><path d="M9.5 9.5L12 7l2.5 2.5"/>',
}


def rotulo(metrica: str, curto: bool = False) -> str:
    return METRICAS[metrica]["curto" if curto else "rotulo"]


def cor(metrica: str) -> str:
    return METRICAS[metrica]["cor"]


def casas(metrica: str) -> int:
    return METRICAS[metrica]["casas"]


def sufixo(metrica: str) -> str:
    return METRICAS[metrica].get("sufixo", "")


def ajuda(metrica: str) -> str:
    return METRICAS[metrica]["ajuda"]


def icone(metrica: str) -> str:
    return ICONES.get(metrica, "")


def so_estados(metrica: str) -> bool:
    return bool(METRICAS[metrica].get("so_estados"))


def regua(metrica: str) -> dict | None:
    """Cortes fixos com nome, quando a métrica tem (o crescimento)."""
    return METRICAS[metrica].get("regua")


def rampa(metrica: str) -> list[str]:
    """Do claro (menos) ao escuro (mais): mais escuro é sempre mais."""
    if regua(metrica) and "rampa" in regua(metrica):
        return regua(metrica)["rampa"]
    return cores.rampa(cor(metrica))
