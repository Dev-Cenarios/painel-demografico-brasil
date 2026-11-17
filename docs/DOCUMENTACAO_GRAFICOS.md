# Documentação dos Gráficos — Dashboard Demográfico

Para cada gráfico do painel, este documento explica três coisas: **por que ele existe**, **como o número é calculado** e **onde está o código**.

Quase todos os gráficos usam a mesma conta de base, feita em `src/charts.py` → `processar_dados()`. Para cada estado ela calcula:

- `total`: a população inteira, de todas as idades;
- `idosos`: quem tem 60 anos ou mais;
- `pct_idosos`: a porcentagem de idosos, ou seja, `idosos ÷ total × 100`.

Essa tabela se chama `df_idosos` no código.

---

## 01 · Mapa: proporção de idosos por estado

**Por que existe:** é a primeira coisa que a pessoa vê. Mostra, de relance, **onde no Brasil a população está mais envelhecida**.

**Como é calculado:** cada estado é pintado de acordo com o seu `pct_idosos`. A cor vai do azul escuro (menos idosos) ao azul claro (mais idosos).

Para o mapa saber qual desenho é de qual estado, ele liga a **sigla** do dado (SP, PE…) à sigla que está no arquivo de contorno dos estados (`featureidkey="properties.sigla"`).

**Código:** `src/charts.py` → `fig_mapa()`

**Plano B:** se o mapa der erro (por exemplo, se o arquivo de contorno não carregar), o `app.py` mostra no lugar um **gráfico de barras** com o mesmo número. Assim a seção nunca fica vazia.

---

## 02 · Top estados: % de idosos

**Por que existe:** no mapa dá para ver o padrão, mas é difícil ler o número exato de cada estado. Esta tabela mostra os valores certinhos.

**Como é calculado:** pega o `df_idosos`, ordena do maior `pct_idosos` para o menor e mostra os **15 primeiros**. Se a pessoa filtrou menos de 15 estados, mostra todos os filtrados.

**Código:** a ordenação é feita no `app.py`, e a tabela é montada em `src/utils.py` → `html_top5()`. O nome da função diz "top 5", mas ela mostra até 15.

---

## 03 · Distribuição por sexo

**Por que existe:** mostra quantos são homens e quantas são mulheres. Com a chave **"Apenas ≥ 60 anos"** ligada, mostra isso só entre os idosos.

**Como é calculado:** soma a população de cada sexo. Quando a chave está ligada, antes de somar, o painel tira todo mundo com menos de 60 anos.

**Código:** `src/charts.py` → `fig_pizza()`

---

## 04 · Pirâmide etária

**Por que existe:** é o gráfico clássico da demografia. **O formato conta a história:**
- base larga e topo fino = população jovem;
- base estreitando e topo engordando = população envelhecendo.

**Como é calculado:** o `processar_dados()` junta as idades em faixas de 5 anos (`0-4`, `5-9`, `10-14`…).

Os homens ficam à esquerda e as mulheres à direita. Para isso, o gráfico desenha os homens como números negativos, que é o jeito comum de fazer pirâmide etária.

> ⚠️ **O topo da pirâmide está errado (achado em out/2026, ainda não corrigido).** No dado do IBGE, a idade `80` quer dizer **80 anos ou mais**. O painel coloca essas pessoas na faixa "80-84". Por isso essa barra fica grande demais (≈ 5 milhões em 2025), e as faixas 85-89, 90-94, 95-99 e 100+ aparecem vazias. O certo seria a última faixa se chamar "80+". Detalhes em [ARQUITETURA.md](ARQUITETURA.md), seção "O que o painel ainda não faz".

**Código:** `src/charts.py` → `fig_piramide()`

---

## 05 · Evolução da população (2010–2025)

**Por que existe:** os outros gráficos mostram **um ano só**. Este mostra **a tendência ao longo do tempo**, dos estados selecionados.

**Como é calculado:**
1. `src/data.py` → `carregar_evolucao()` soma a população de cada estado em cada ano. Esse resultado fica guardado na memória e **não muda com o filtro de ano**, porque o gráfico sempre mostra a série inteira.
2. `fig_evolucao()` soma só os estados que a pessoa escolheu e mostra o resultado **em milhões de habitantes**.

**Código:** `src/charts.py` → `fig_evolucao()`

---

## 06 · Ranking: proporção de idosos por estado

**Por que existe:** usa o mesmo número do mapa e da tabela Top 15, mas mostra **todos os estados** em barras. Serve para comparar o conjunto inteiro, não só os que estão no topo.

**Como é calculado:** usa o mesmo `df_idosos` do mapa, ordenado **do menor para o maior**. Parece invertido, mas é de propósito: no Plotly, as barras deitadas são desenhadas de baixo para cima, então essa ordem deixa o **maior valor no topo** da tela.

**Código:** `src/charts.py` → `fig_ranking()`

---

## Números de destaque (os 4 cartões do topo)

São quatro cartões:

| Cartão | Como é calculado |
|---|---|
| **População total** | Soma da população dos estados selecionados. |
| **Proporção de idosos** | População com 60+ ÷ população total × 100. |
| **Proporção feminina** | População feminina ÷ população total × 100. |
| **Idade média** | Média das idades, com o peso da população de cada idade. |

Todos são calculados no `app.py`, já com o filtro de estados aplicado (tabela `df_filt`).

**Comparação com o ano anterior:** cada cartão mostra uma setinha (▲ ou ▼) com a variação em relação ao ano anterior. Quem monta isso é o `src/utils.py` → `_delta_html()`. Dois cuidados na hora de ler:

- **A variação é relativa, em %.** Se a proporção de idosos foi de 15,0% para 15,5%, o cartão mostra **▲ 3,3%**, não "+0,5 ponto".
- **No primeiro ano da série (2010) não aparece variação**, porque não tem ano anterior para comparar.

> ⚠️ **A idade média sai um pouco menor do que a real.** É o mesmo problema da pirâmide: todo mundo com 80 anos ou mais entra na conta como se tivesse exatamente 80.
