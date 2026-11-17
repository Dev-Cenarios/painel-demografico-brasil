# Arquitetura — Dashboard Demográfico

Este documento explica como o painel funciona por dentro, do começo ao fim. É para quem vai rodar, mudar ou cuidar do projeto sem ter a pessoa que construiu do lado.

## Como o dado chega na tela

O caminho é este, de cima para baixo:

```
IBGE (Projeções de População 2010-2025)
        │
        │  O tratamento dos dados NÃO está neste repositório.
        │  Os arquivos .parquet da pasta data/ já chegam prontos.
        ▼
data/pop_ibge.parquet ─────────┐
data/ibge_municipios.parquet ──┼─► src/data.py → _carregar_base()
data/ibge_ufs.parquet ─────────┘   junta os 3 arquivos numa tabela só
        │
        ▼
src/data.py → carregar_dados(), carregar_evolucao(), anos_disponiveis()
        │  guardam o resultado na memória, para não reler o arquivo a cada clique
        ▼
src/charts.py → processar_dados()
        │  agrupa as idades em faixas de 5 anos e separa os idosos de cada estado
        ▼
app.py → monta a barra lateral e os filtros e chama:
        │   src/charts.py → fig_*()   para desenhar cada gráfico
        │   src/utils.py              para os cartões de números e as tabelas
        │   src/themes.py             para as cores e o tema claro/escuro
        ▼
Streamlit mostra tudo no navegador
```

### O que acontece em cada passo

1. **Leitura e junção (`_carregar_base`).** O arquivo de população vem por **município**. Para chegar ao **estado**, o painel usa os outros dois arquivos:
   - `ibge_municipios.parquet` diz a que estado cada município pertence;
   - `ibge_ufs.parquet` traz a sigla de cada estado (DF, SP, PE…).

   Nessa mesma etapa, o sexo vem do IBGE como `"1"` e `"2"` e vira `"M"` e `"F"`, e a idade, que vem como texto (`"005"`), vira número (`5`).

2. **Memória (cache).** As funções de `src/data.py` usam `@st.cache_data` e `@st.cache_resource`. Isso faz o Streamlit guardar o resultado depois da primeira leitura. Nos cliques seguintes, o painel pega da memória em vez de abrir o arquivo de novo. O contorno dos estados (`carregar_geojson`) também fica guardado assim.

3. **Preparação para os gráficos (`processar_dados`).** A idade vem ano a ano (0, 1, 2… 80). Aqui ela é agrupada em faixas de 5 anos para a pirâmide, e o painel calcula a porcentagem de idosos (60+) de cada estado, usada no mapa e no ranking.

4. **Montagem da tela (`app.py`).** Lê os filtros que a pessoa escolheu e chama cada função de gráfico.

### Limitação importante: atualizar os dados

O processo que transforma o dado bruto do IBGE nesses 3 arquivos **não está neste repositório**.

Então, quando o IBGE lançar uma projeção nova (por exemplo, a de 2026), não basta rodar um comando aqui. É preciso:

1. refazer esse tratamento fora deste projeto;
2. trocar os arquivos da pasta `data/`;
3. **manter as mesmas colunas**, senão o `_carregar_base()` quebra.

As colunas que o painel espera:

| Arquivo | Colunas |
|---|---|
| `pop_ibge.parquet` | `cod_mun`, `ano`, `idade`, `sexo`, `populacao` |
| `ibge_municipios.parquet` | `id` (código do município), `ibge_uf_id` (código do estado) |
| `ibge_ufs.parquet` | `id` (código do estado), `sigla`, `nome` |

## Para que serve cada arquivo de código

| Arquivo | O que faz |
|---|---|
| `app.py` | Arquivo principal. Monta a barra lateral, os filtros e a página, e chama os outros módulos. |
| `src/data.py` | Lê os arquivos de dados e guarda na memória. **É o único arquivo que lê do disco.** |
| `src/charts.py` | Prepara os dados (`processar_dados`) e desenha os gráficos com Plotly. |
| `src/utils.py` | Formata números, monta os cartões de destaque e as tabelas em HTML, e aplica o visual padrão dos gráficos. |
| `src/themes.py` | Cores do tema claro e escuro, o estilo (CSS) da página e o botão de trocar de tema. |

**Não tem API nem banco de dados.** Tudo roda dentro do próprio Streamlit, lendo os arquivos `.parquet` da pasta `data/`.

## Configuração

**Não precisa de nenhuma variável de ambiente.** O painel não usa senha, banco ou serviço externo.

A única configuração que importa está em `.streamlit/config.toml`:

```toml
baseUrlPath = "cenarios/demografico"
```

Esse é o "endereço" do painel dentro do site. **Ele precisa ser igual à rota configurada no nginx do servidor**, senão o painel não abre.

## Publicação (deploy)

- **Imagem Docker:** o `docker-compose.yml` monta a imagem a partir do `Dockerfile` (Python 3.11-slim + Streamlit).
- **O código vai dentro da imagem** (`COPY . .`). Só a pasta `data/` fica de fora: ela é ligada ao container de fora para dentro, em modo **somente leitura**.
- **Container:** `dashboard-demografico`, porta **8501**. A porta só abre para o próprio servidor (`127.0.0.1`). Quem vem de fora passa pelo nginx.
- **No servidor:** a pasta é `~/dashboard-demografico/`, e o nginx publica em `https://painel.cenarios.unb.br/cenarios/demografico` (repassando para `localhost:8501`).

**Mudou o código? Tem que reconstruir a imagem.** Como o código foi copiado para dentro da imagem, editar `app.py` ou `src/` não muda o painel que está rodando. É preciso rodar:

```bash
docker compose up -d --build
```

## O que o painel ainda não faz

- **O tratamento dos dados não está aqui.** Veja "Limitação importante" acima.
- **Não tem testes automáticos.** Para saber se um número está certo, é preciso conferir no painel.
- **Só mostra estados, não municípios.** Os dados vêm por município, mas o painel sempre soma por estado. Para ter visão municipal, seria preciso criar os filtros e gráficos para isso.
- **Período:** 2010 a 2025.
- **O topo da pirâmide está errado (achado em out/2026, ainda não corrigido).** No arquivo do IBGE, a idade `80` quer dizer **80 anos ou mais**. Em 2025 são 4,96 milhões de pessoas, contra 755 mil com 79 anos. Só que o `processar_dados()` monta faixas até "100+" e coloca o 80 na faixa "80-84". Por isso a barra **"80-84" mostra todo mundo com 80 ou mais** e fica grande demais, e as barras 85-89, 90-94, 95-99 e 100+ aparecem vazias. A correção é a última faixa ser "80+" (em `processar_dados()` e na lista `FAIXAS` de `fig_piramide()`). A porcentagem de idosos (60+) **não é afetada**, porque ela soma tudo de 60 para cima.
