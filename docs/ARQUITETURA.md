# Arquitetura — Painel Demográfico

Este documento explica como o painel funciona por dentro, do começo ao fim. É para quem vai rodar, mudar ou cuidar do projeto sem ter a pessoa que construiu do lado.

## Como o dado chega na tela

O caminho é este, de cima para baixo:

```
IBGE (população)          SINASC/DATASUS (nascimentos)     IBGE (esperança de vida)
      │                          │                                 │
      │ tratamento fora          │ scripts/preparar_nascimentos.py │ veio do painel de
      │ deste repositório        │                                 │ Envelhecimento
      ▼                          ▼                                 ▼
data/pop_ibge.parquet     data/nascimentos.parquet       data/esperanca_vida_uf.parquet
data/ibge_ufs.parquet            │                                 │
      │                          │                                 │
      └──────────────┬───────────┴─────────────────────────────────┘
                     ▼
src/dados.py  →  DuckDB lê os Parquet direto e faz todas as contas
                 (indicadores por Brasil, estado, município e ano)
                     │
                     ▼
app.py  →  guarda os resultados na memória (cache do Streamlit)
           e monta a tela com as peças do cenarios_core:
             mapa.deck() + mapa_componente   → o mapa (deck.gl)
             grafico_componente              → os gráficos (ECharts)
             src/graficos.py                 → pirâmide com dois anos, grupos de idade
             src/estilo.py + src/theme/      → cabeçalho, números de destaque, cores
                     │
                     ▼
Streamlit mostra tudo no navegador
```

### O que acontece em cada passo

1. **As contas (`src/dados.py`).** O painel não carrega a base inteira na memória. A cada pedido, o DuckDB lê do Parquet só o que precisa e devolve a conta pronta. A população tem 14,4 milhões de linhas, e mesmo assim cada conta leva uns 30 milésimos de segundo.

   **Uma conta só serve para tudo.** A mesma consulta calcula todos os indicadores de estrutura (grupos de idade, dependência, razão de sexo, idade mediana) e muda só o agrupamento: Brasil, estado, município ou ano. Assim, o número do card, o do mapa e o da série histórica nunca saem de contas diferentes. Os testes conferem isso.

2. **O recorte.** É o lugar que está na tela:
   - **Brasil:** nenhum lugar escolhido;
   - **estado:** a sigla (`"SP"`);
   - **município:** os 6 primeiros dígitos do código do IBGE (`"355030"`), o mesmo código da malha do mapa.

   Clicar no mapa ou no ranking troca o recorte. Clicar de novo no mesmo lugar volta um nível.

3. **Memória (cache).** O `app.py` guarda o resultado de cada conta com `@st.cache_data`. No segundo clique no mesmo lugar, o número já está pronto. O contorno dos municípios também fica guardado (`@st.cache_resource`).

4. **A tela (`app.py`).** Lê o ano, o tema, o indicador e o lugar, e desenha. Cada bloco (cada card, o mapa, cada aba) roda dentro de `resiliencia.painel()`, do `cenarios_core`: **se um bloco der erro, só ele mostra um aviso**, e o resto do painel continua funcionando.

## Os arquivos de dados

| Arquivo | O que tem | Colunas | De onde vem |
|---|---|---|---|
| `data/pop_ibge.parquet` | população por município, ano, sexo e idade simples | `cod_mun`, `ano`, `sexo` (`"1"` homem, `"2"` mulher), `idade` (texto, `"000"` a `"080"`), `populacao` | IBGE. O tratamento **não está neste repositório** |
| `data/ibge_ufs.parquet` | os 27 estados | `id` (código), `sigla`, `nome` | IBGE |
| `data/nascimentos.parquet` | nascidos vivos por município de residência da mãe, ano e idade da mãe | `cod6`, `ano`, `idade_mae` (vazia quando ignorada), `n` | SINASC, gerado por `scripts/preparar_nascimentos.py` |
| `data/esperanca_vida_uf.parquet` | esperança de vida ao nascer e aos 60, por estado e ano | `uf`, `ano`, `e0_T`, `e0_H`, `e0_M`, `e60_T`, `e60_H`, `e60_M` | IBGE, Projeções da População 2024 (tabela 4) |
| `geo/municipios.parquet` | contorno dos 5.571 municípios | `cod_mun6`, `nome_mun`, `uf`, `geometry` | malha do IBGE, a mesma do painel de tuberculose no Brasil |
| `geo/ufs.parquet` | contorno dos 27 estados | `uf`, `nome_uf`, `geometry` | idem |

**A idade `80` quer dizer "80 anos ou mais".** É assim que o arquivo de população vem. Por isso a pirâmide termina na faixa "80+" e não vai até 100.

## Como atualizar os dados

Cada fonte se atualiza de um jeito:

### Nascimentos (SINASC)

Quando o DATASUS fechar um ano novo:

```bash
python scripts/preparar_nascimentos.py <pasta temporária>
```

O script baixa o arquivo nacional de cada ano (`DNBR<ano>.dbc`, de 100 a 210 MB cada), soma os nascimentos, **apaga o arquivo baixado** antes de ir para o ano seguinte e no fim grava `data/nascimentos.parquet` (uns 3,4 MB). De 2010 a 2024 leva uns 8 minutos.

**Precisa de Python 3.11 ou 3.12**, por causa do `pyreaddbc`, que lê o formato DBC do DATASUS. No 3.13 ou mais novo ele tenta compilar e falha no Windows. O painel em si não usa o `pyreaddbc`, então essa versão de Python é só para rodar o script.

Os cuidados que o script toma estão escritos no começo dele (idade 99 é "ignorado", código de município com 7 dígitos etc.).

**Conferido em 17/nov/2026:** os 42.053.253 nascidos vivos de 2010 a 2024 batem com o banco `cenarios_ai` da equipe, em todas as 2,2 milhões de combinações de ano, município e idade da mãe. Um aviso: a tabela `public.sinasc` desse banco tem linhas duplicadas em 2017 e 2024, de cargas que pararam no meio. Contando direto dela, esses dois anos saem inflados. Quem usar o banco precisa ficar só com a carga marcada como `SUCESSO` no `log_ingestao_sinasc`.

### Esperança de vida

O arquivo é um recorte de 2010 a 2025 do `data/indicadores_uf.parquet` do painel de Envelhecimento, que é gerado pelo `scripts/preparar_projecao.py` de lá. Quando o IBGE publicar uma revisão nova das projeções, gere o arquivo lá e copie para cá com as mesmas colunas.

### População

O tratamento que gera o `pop_ibge.parquet` **não está neste repositório**. Para trocar a base, é preciso refazer o arquivo fora daqui **com as mesmas colunas**. Senão, a consulta do `src/dados.py` quebra.

## Para que serve cada arquivo de código

| Arquivo | O que faz |
|---|---|
| `app.py` | Monta a tela: cabeçalho, números de destaque, controles, mapa e as quatro abas. Lê os cliques no mapa e no ranking. **Não faz conta**: pede tudo ao `src/dados.py`. |
| `src/dados.py` | Todas as contas, com DuckDB. **É o único arquivo que lê `data/` e `geo/`.** |
| `src/indicadores.py` | A ficha de cada indicador: nome, cor, casas decimais, explicação, ícone e régua fixa, quando tem. Também os temas do mapa. Para mudar o nome ou a cor de um indicador, é aqui. |
| `src/graficos.py` | Os gráficos que são só deste painel, montados em cima dos do `cenarios_core`: a pirâmide com outro ano em contorno, os grupos de idade, a dependência e a frase do bônus demográfico. |
| `src/estilo.py` | O cabeçalho, os números de destaque (com a variação sem verde nem vermelho) e o rodapé. |
| `src/theme/` | O visual comum dos painéis Cenários (cores, cartões, espaçamento). Veio igual do painel de tuberculose no Brasil. |
| `scripts/preparar_nascimentos.py` | Baixa o SINASC e gera `data/nascimentos.parquet`. Roda só para atualizar o dado. |

**Não tem API nem banco de dados.** Tudo roda dentro do próprio Streamlit, lendo os arquivos `.parquet`.

## Configuração

**Não precisa de nenhuma variável de ambiente.** O painel não usa senha, banco ou serviço externo.

A configuração que importa está em `.streamlit/config.toml`:

```toml
baseUrlPath = "cenarios/demografico"
```

Esse é o "endereço" do painel dentro do site. **Ele precisa ser igual à rota configurada no nginx do servidor**, senão o painel não abre.

O mesmo arquivo prende o **tema claro**, igual ao dos outros painéis.

## Publicação (deploy)

- **Imagem Docker:** o `Dockerfile` usa `python:3.13-slim` e instala as versões exatas do `requirements.lock.txt`, incluindo o `cenarios_core` da pasta `vendor/`. Por isso o build não depende de baixar o núcleo de lugar nenhum.
- **O código vai dentro da imagem** (`app.py`, `src/`, `geo/`, `assets/`). A pasta `data/` fica de fora: ela é ligada ao container de fora para dentro, em modo **somente leitura**.
- **Container:** `dashboard-demografico`, porta **8501**. A porta só abre para o próprio servidor (`127.0.0.1`). Quem vem de fora passa pelo nginx.
- **No servidor:** o nginx publica em `https://painel.cenarios.unb.br/cenarios/demografico`, repassando para `localhost:8501`.

**Mudou o código? Tem que reconstruir a imagem:**

```bash
docker compose up -d --build
```

Isso também **recria o container**, e isso importa: o Streamlit guarda as contas na memória pelo nome da função. Se só a conta mudou, um container antigo continua mostrando o número velho. Na reforma de novembro de 2026, isso fez os cards novos aparecerem vazios até o servidor ser reiniciado.

**Mudou só um arquivo de `data/`?** Basta reiniciar o container (`docker compose restart`), pelo mesmo motivo.

**Depois de todo deploy, abra o painel e confira um número conhecido.** Por exemplo, Brasil 2025 tem 213.421.037 habitantes. O healthcheck do Docker responde "ok" mesmo com o painel quebrado.

## O que o painel ainda não faz

- **O tratamento da população não está aqui.** Veja "Como atualizar os dados".
- **A população vai até 2025 e vem de uma base mais antiga** que a do painel de Envelhecimento, que usa a revisão de 2024 das projeções do IBGE (2000 a 2070, idade até 90+). Só que essa revisão não tem município, e este painel precisa dele.
- **A esperança de vida do Brasil é uma aproximação:** é a média dos estados, com o peso da população. O número oficial do Brasil está na mesma planilha do IBGE (linha do Brasil), mas o arquivo do painel de Envelhecimento guardou só os estados.
- **A fecundidade não corrige o sub-registro.** Ela sai dos nascimentos registrados no SINASC divididos pelas mulheres de 15 a 49 anos. O IBGE corrige os nascimentos que não chegam a ser registrados, sobretudo no Norte, por isso o número oficial dele fica um pouco acima.
- **Não tem mortes nem migração.** Os próximos passos seriam o SIM (óbitos e mortalidade infantil) e a migração dos Censos de 2010 e 2022.
- **O SINASC de 2025 ainda é preliminar** no DATASUS e não entrou.

## Por que o painel mudou (novembro de 2026)

Até outubro de 2026, o painel era em Plotly, com barra lateral, tema escuro e mapa em Mapbox (Carto). Ele mostrava praticamente só envelhecimento: % de 60+, pizza por sexo, uma tabela Top 15 e um ranking que repetiam o mapa. Também tinha dois erros: o topo da pirâmide tratava "80 ou mais" como "80 a 84", e o mapa tinha as cores invertidas (mais escuro = menos idosos).

A reforma fez quatro coisas:

1. **Mesma cara dos outros painéis:** passou a usar o `cenarios_core`, com mapa deck.gl clicável até o município.
2. **Foco na população inteira:** saíram os indicadores de envelhecimento, que são do painel irmão. Entraram crescimento, densidade, grupos de idade, dependência, esperança de vida e nascimentos.
3. **Correção dos erros:** a pirâmide termina em "80+", e no mapa mais escuro é sempre mais. A idade média, que saía puxada para baixo pelo "80+", virou idade mediana.
4. **Testes:** passou a ter testes automáticos, que antes não existiam.
