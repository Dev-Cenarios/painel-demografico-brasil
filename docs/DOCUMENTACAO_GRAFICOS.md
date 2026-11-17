# Documentação dos Gráficos — Painel Demográfico

Para cada parte do painel, este documento explica três coisas: **por que ela existe**, **como o número é calculado** e **onde está o código**.

Todas as contas ficam em `src/dados.py`. O nome, a cor e a explicação de cada indicador ficam em `src/indicadores.py`.

---

## Os indicadores

Valem para o Brasil, um estado ou um município, em qualquer ano. Os exemplos são do Brasil.

### Estrutura (quem é a população)

| Indicador | Como é calculado | Brasil, 2025 |
|---|---|---:|
| **População** | Soma de todas as idades e dos dois sexos. | 213.421.037 |
| **% de crianças (0 a 14)** | Pessoas de 0 a 14 anos ÷ população × 100. | 19,5% |
| **% de idosos (65+)** | Pessoas com 65 anos ou mais ÷ população × 100. | 11,6% |
| **Razão de dependência** | (0 a 14 + 65 ou mais) ÷ (15 a 64) × 100. Quantas pessoas fora da idade de trabalhar há para cada 100 em idade de trabalhar. | 45,0 |
| **Idade mediana** | A idade que divide a população ao meio: metade tem menos, metade tem mais. | 35,7 anos |
| **Razão de sexo** | Homens ÷ mulheres × 100. Abaixo de 100, há mais mulheres. | 95,1 |

**Por que idade mediana e não idade média.** O arquivo do IBGE junta todo mundo com 80 anos ou mais na idade `80`. Na média, uma pessoa de 95 anos contaria como se tivesse 80, e o resultado sairia puxado para baixo. A mediana não sofre com isso, porque a metade da população fica longe dos 80.

**Como a mediana é achada.** A idade vem ano a ano. O painel soma as pessoas de 0, 1, 2… anos até passar da metade, e dentro dessa idade divide proporcionalmente. Por isso ela tem casa decimal (35,7), e não só número inteiro.

### Crescimento

| Indicador | Como é calculado | Brasil, 2025 |
|---|---|---:|
| **Crescimento anual** | (população do ano ÷ população do ano anterior − 1) × 100. Em 2010, primeiro ano da base, fica vazio. | +0,39% |
| **Densidade** | População ÷ área em km². | 25,1 hab./km² |

**De onde vem a área.** Do próprio contorno de cada município (`geo/municipios.parquet`), medido numa projeção que preserva área (Albers da América do Sul). A área de um estado é a soma dos municípios dele, e a do Brasil é a soma de todos. Dá 8,51 milhões de km², que é a área oficial do Brasil. Os testes conferem isso, e também os 5.760 km² do DF.

### Nascimentos (SINASC)

| Indicador | Como é calculado | Brasil, 2024 |
|---|---|---:|
| **Nascidos vivos** | Nascimentos de mães que **moram** no lugar, mesmo que o parto tenha sido em outra cidade. | 2.389.325 |
| **Natalidade** | Nascidos vivos ÷ população × 1.000. | 11,2 por mil |
| **Fecundidade** | Quantos filhos, em média, uma mulher teria na vida se as taxas do ano valessem para sempre. A conta está logo abaixo. | 1,49 filho |
| **Mães adolescentes** | Nascimentos de mães com menos de 20 anos ÷ nascimentos com a idade da mãe informada × 100. | 11,4% |
| **Idade média da mãe** | Média da idade da mãe no parto. | 27,8 anos |

**A conta da fecundidade (taxa de fecundidade total).**

1. Para cada faixa de 5 anos da mãe (15 a 19, 20 a 24… 45 a 49), divide os nascimentos pelo número de mulheres daquela faixa.
2. Soma as sete taxas e multiplica por 5, porque cada faixa tem 5 anos.
3. As mães de 10 a 14 anos entram na faixa de 15 a 19, e as de 50 ou mais na de 45 a 49. Sem isso, esses nascimentos sumiriam da conta.
4. Os nascimentos com a idade da mãe ignorada (no máximo 0,01% em cada ano) são distribuídos na mesma proporção dos outros.

**2,1 filhos por mulher é a "reposição":** o número com que a população se mantém sozinha, sem contar a migração. O Brasil está abaixo disso desde antes de 2010.

**O SINASC vai até 2024.** Num ano que ele ainda não tem, o número de destaque e o mapa mostram o último ano fechado, e a tela diz qual é.

**Esta fecundidade não corrige o sub-registro.** O IBGE corrige os nascimentos que não chegam a ser registrados, por isso o número oficial dele fica um pouco acima.

### Mortalidade

| Indicador | Como é calculado | Brasil, 2025 |
|---|---|---:|
| **Esperança de vida ao nascer** | Quantos anos, em média, viveria quem nasce no ano, se as taxas de morte daquele ano se mantivessem. Vem pronta do IBGE (Projeções da População, revisão 2024). | 76,9 anos |

**O IBGE publica por estado, não por município.** Por isso:

- **no mapa**, este indicador fica sempre nos 27 estados, e o botão "Municípios" fica desligado;
- **num município**, o número de destaque mostra o valor do estado e diz isso ("valor de SP");
- **no Brasil**, o número é a média dos estados, com o peso da população de cada um. É uma aproximação, e a tela avisa ("média dos estados").

A queda da covid aparece na série: 76,3 anos em 2019, 72,9 em 2021 e 76,9 em 2025.

---

## Números de destaque (os 6 cartões do topo)

São seis: **população, crescimento anual, fecundidade, esperança de vida, idade mediana e densidade**. Os outros indicadores estão no mapa.

**Comparação com o ano anterior.** Cada cartão mostra uma seta com quanto o número mudou. O jeito de medir depende do indicador:

| Indicador | Como a mudança é escrita | Exemplo |
|---|---|---|
| População | em %, a mudança relativa | ↑ 0,4% |
| Indicadores em % (crescimento, % de crianças etc.) | em **pontos percentuais** (p.p.), a diferença direta | ↓ 0,03 p.p. |
| Os outros | a diferença, na unidade do indicador | ↑ 0,4 (anos) |

**Por que pontos percentuais.** Se a % de idosos vai de 15,0% para 15,5%, ela subiu **0,5 ponto**. Escrever "subiu 3,3%" (a mudança relativa) confunde. A versão antiga do painel fazia assim.

**A seta não tem verde nem vermelho.** Em demografia, subir ou descer não é bom nem ruim em si. A fecundidade cair, por exemplo, não é uma notícia boa nem má. Quando a mudança some no arredondamento, o cartão escreve "≈ igual a 2024".

**Código:** os cartões são montados no `app.py`, e a variação em `src/estilo.py` → `variacao()`.

---

## Mapa

**Por que existe:** mostra de relance **onde** cada indicador é alto ou baixo.

**Como funciona:**

- **Tema e indicador.** Primeiro se escolhe o tema (Estrutura, Crescimento, Nascimentos, Mortalidade) e depois o indicador. Com tudo numa linha só, os 11 indicadores não cabiam.
- **Estados e municípios.** O mapa abre nos 27 estados. Clicando num estado, aparecem os municípios dele, e todo o painel passa a mostrar aquele estado. Clicando num município, o painel mostra o município. Clicando de novo no mesmo lugar, volta um nível. O botão "Municípios" mostra os 5.571 municípios do Brasil de uma vez, com o contorno dos estados por cima.
- **As cores.** Mais escuro é sempre "mais". O painel oferece dois jeitos de dividir as faixas:
  - **Quintis** (o padrão): cinco faixas com o mesmo número de lugares em cada. É o que funciona com 5.571 municípios: densidade e crescimento têm pontas tão longas que, com outro método, quase tudo cairia numa cor só.
  - **Quebras naturais:** as faixas seguem os "buracos" naturais dos valores.
- **Régua fixa.** Dois indicadores têm faixas fixas, iguais em todo ano, porque um ponto da escala tem significado próprio:
  - **crescimento:** o zero separa quem cresce de quem encolhe. A cor é **divergente**: vermelho encolhe, azul cresce. Faixas: encolhe mais de 1% · encolhe · cresce pouco (0 a 0,5%) · cresce · cresce mais de 1%;
  - **fecundidade:** o 2,1 da reposição. Faixas: muito baixa (abaixo de 1,5) · baixa · abaixo da reposição · acima da reposição · alta (2,5 ou mais).
- **Legenda.** Mostra quantos lugares caem em cada faixa.
- **Ao passar o mouse,** aparecem o nome do lugar, o valor e a população.

**Código:** `app.py`, na seção "Mapa", usando `mapa.deck()`, `mapa.legenda()` e `mapa_componente` do `cenarios_core`. O mapa é deck.gl: o `cenarios_core` saiu do Plotly porque o mapa do Plotly não avisa o painel quando alguém clica.

---

## Aba 1 · Pirâmide etária

**Por que existe:** é o gráfico clássico da demografia. **O formato conta a história:**

- base larga e topo fino = população jovem;
- base estreitando e topo engordando = população envelhecendo.

**Como é calculada:** as idades são juntadas em faixas de 5 anos (0 a 4, 5 a 9… 75 a 79). **A última faixa é "80+"**, porque é assim que o dado vem. Os homens ficam à esquerda e as mulheres à direita, na mesma escala dos dois lados.

**Comparar com outro ano.** O outro ano aparece como **contorno** por cima das barras. Onde o contorno passa da barra, aquela idade tinha mais gente no outro ano. Abre comparando com 2010. Para o Brasil, a base mais estreita e o topo mais largo em 2025 aparecem logo de cara.

**"Em % da população".** Com essa chave ligada, cada barra é o percentual da população, e homens e mulheres somam 100. Serve para comparar a **forma** da pirâmide entre lugares de tamanhos muito diferentes, ou entre anos com populações diferentes.

**Código:** `src/dados.py` → `piramide()` e `src/graficos.py` → `piramide()`. Ele usa a pirâmide do `cenarios_core` e acrescenta o contorno.

---

## Aba 2 · Grupos de idade

**Por que existe:** a pirâmide mostra um ano. Esta aba mostra **o movimento**: como os três grandes grupos de idade mudam ao longo dos anos.

**Gráfico 1, crianças, idade de trabalhar e idosos.** Colunas empilhadas em 100%: em cada ano, quanto da população tem 0 a 14, 15 a 64 e 65 anos ou mais.

**Gráfico 2, razão de dependência.** Três linhas:

- **Total:** (crianças + idosos) para cada 100 de 15 a 64;
- **Jovens:** só as crianças;
- **Idosos:** só os idosos.

O total é a soma das outras duas.

**O bônus demográfico.** Enquanto a dependência total cai, há proporcionalmente mais gente em idade de trabalhar. É a "janela" do bônus demográfico. Ela fecha quando a subida dos idosos passa a compensar a queda das crianças. Embaixo do gráfico, uma frase diz onde o lugar está:

| Situação | O que a frase diz |
|---|---|
| a dependência só caiu | a janela ainda está aberta |
| caiu, chegou a um mínimo e voltou a subir | a janela está se fechando, e diz o ano do mínimo |
| só subiu desde 2010 | a janela já tinha fechado |

No Brasil, o mínimo foi em **2017 (44,4)**.

**Código:** `src/graficos.py` → `grupos_por_ano()`, `dependencia_por_ano()` e `frase_bonus()`.

---

## Aba 3 · Evolução temporal

**Por que existe:** mostra a tendência do indicador escolhido no mapa, de 2010 até o último ano, no lugar que está na tela.

**Como é:**

- em geral, colunas por ano, com o ano escolhido destacado;
- **fecundidade:** linha, com a **reposição (2,1)** tracejada;
- **esperança de vida:** três linhas, total, homens e mulheres. A diferença entre os dois sexos faz parte da história;
- **embaixo**, a contagem que dá base ao indicador: **nascidos vivos** no tema Nascimentos e **população** nos outros. Em milhões ou em mil, conforme o tamanho do lugar.

**Código:** `app.py`, na aba "Evolução temporal". A série inteira vem de uma consulta só: `src/dados.py` → `serie()`.

---

## Aba 4 · Ranking

**Por que existe:** no mapa dá para ver o padrão, mas não o número exato. O ranking mostra os valores e deixa comparar.

**Como é:**

- **com o mapa nos estados:** os 27, do maior para o menor;
- **com o mapa nos municípios:** os 10 municípios com o maior valor, no Brasil ou no estado aberto;
- **a linha tracejada** é o valor do Brasil;
- **a cor de cada barra** é a faixa do mapa;
- **dá para clicar numa barra**, igual a clicar no mapa.

**Cuidado com município pequeno:** com poucos habitantes, um indicador vai lá em cima ou lá embaixo com facilidade. O painel avisa embaixo do ranking. Confira a população do lugar, que aparece ao passar o mouse no mapa.

**Código:** `src/dados.py` → `ranking()` e o `ranking` do `cenarios_core` (`grafico_componente.ranking`).
