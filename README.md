# Painel Demográfico — Brasil

Este painel mostra **como é a população brasileira e como ela está mudando**: quantas pessoas há em cada lugar, de que idade e de que sexo, quanto cada lugar cresce ou encolhe, quantos filhos as mulheres têm e quanto tempo se vive.

Dá para ver o Brasil, um estado ou um município, de 2010 a 2025.

![preview do painel](docs/preview.png)

**No ar:** <https://painel.cenarios.unb.br/cenarios/demografico/>

## O que tem no painel

- **Seis números de destaque** no topo: população, crescimento anual, fecundidade, esperança de vida, idade mediana e densidade. Cada um compara com o ano anterior.
- **Mapa do Brasil** que abre nos estados. Clicando num estado, aparecem os municípios dele. Também dá para ver os 5.571 municípios do país de uma vez.
- **Pirâmide etária**, com o contorno de outro ano por cima (por exemplo, 2025 contra 2010). O que a população ganhou ou perdeu em cada idade fica visível.
- **Grupos de idade**: crianças (0 a 14), idade de trabalhar (15 a 64) e idosos (65+) ano a ano, e a razão de dependência com uma frase sobre o **bônus demográfico**.
- **Evolução no tempo** do indicador escolhido, de 2010 até o último ano.
- **Ranking** dos estados, ou dos 10 municípios com o maior valor, com a linha do Brasil para comparar.

Todos os números mudam juntos quando você escolhe um ano ou clica num lugar.

## Os indicadores

O mapa escolhe primeiro o **tema** e depois o **indicador**:

| Tema | Indicadores |
|---|---|
| **Estrutura** | % de crianças (0 a 14), % de idosos (65+), razão de dependência, idade mediana, razão de sexo |
| **Crescimento** | crescimento anual, densidade |
| **Nascimentos** | fecundidade (filhos por mulher), natalidade, % de mães adolescentes, idade média da mãe |
| **Mortalidade** | esperança de vida ao nascer |

Como cada um é calculado está em [Documentação dos Gráficos](docs/DOCUMENTACAO_GRAFICOS.md).

**Por que não tem % de 60+ nem índice de envelhecimento?** Porque o envelhecimento em detalhe é o assunto do painel irmão, o [Envelhecimento Populacional no Brasil](https://github.com/Dev-Cenarios/painel-envelhecimento-brasil). Este aqui olha para a população inteira.

## De onde vêm os dados

| Dado | Fonte | Período | Nível |
|---|---|---|---|
| População por sexo e idade | IBGE | 2010 a 2025 | município |
| Nascidos vivos | **SINASC**, do DATASUS (Ministério da Saúde) | 2010 a 2024 | município de residência da mãe |
| Esperança de vida | IBGE, Projeções da População, revisão 2024 | 2010 a 2025 | estado |
| Contorno dos municípios e estados | Malha do IBGE | — | município e estado |

Três avisos:

- **O SINASC vai até 2024.** O DATASUS fecha cada ano com atraso. Em 2025 o painel mostra os nascimentos de 2024 e diz isso no próprio número.
- **A esperança de vida só existe por estado.** O IBGE não calcula por município. Num município o painel mostra o número do estado. Para o Brasil, o painel usa a média dos estados, com o peso da população de cada um. As duas coisas vêm escritas na tela.
- **Num município pequeno, as taxas pulam muito de um ano para o outro.** Três nascimentos a mais numa cidade de 2 mil habitantes já mudam a fecundidade. Compare sempre com os anos vizinhos.

Como cada arquivo é gerado e como atualizar está em [Arquitetura](docs/ARQUITETURA.md).

## Onde ler mais

| Documento | O que explica |
|---|---|
| [Arquitetura](docs/ARQUITETURA.md) | Como o dado sai do arquivo e chega na tela, para que serve cada arquivo de código, como atualizar os dados e como publicar. **Comece por aqui.** |
| [Documentação dos Gráficos](docs/DOCUMENTACAO_GRAFICOS.md) | Por que cada gráfico existe, como cada número é calculado e onde está o código. |

## Ferramentas usadas

| Parte | Ferramenta |
|---|---|
| Tela do painel | Streamlit |
| Mapa | deck.gl, pelo `cenarios_core` (o núcleo comum dos painéis Cenários) |
| Gráficos | ECharts, também pelo `cenarios_core` |
| Contas | DuckDB, direto nos arquivos Parquet. Cada conta leva poucos centésimos de segundo |

O `cenarios_core` é o mesmo dos painéis de tuberculose e hanseníase, por isso os painéis têm a mesma cara. Ele vem pronto, numa versão fixa, na pasta `vendor/`.

## Como rodar no seu computador

```bash
git clone https://github.com/Dev-Cenarios/painel-demografico-brasil.git
cd painel-demografico-brasil
pip install -r requirements.lock.txt
streamlit run app.py
```

Depois é só abrir `http://localhost:8501/cenarios/demografico/` no navegador. O `/cenarios/demografico/` no fim vem do `.streamlit/config.toml`, que imita o endereço do servidor.

Use **Python 3.13**, a mesma versão do servidor (imagem Docker `python:3.13-slim`).

## Testes

```bash
python -m pytest -q
```

São 40 testes. Eles conferem, entre outras coisas:

- se o total de nascidos vivos bate com o publicado pelo DATASUS (2010, 2015 e 2020);
- se a esperança de vida de um estado é a da planilha do IBGE;
- se os estados somam o Brasil e os municípios somam o estado;
- se a pirâmide termina em "80+" e fecha com a população;
- se o painel abre sem erro em todos os indicadores e com um estado ou município escolhido.

A cada envio para o GitHub, o [CI](.github/workflows/ci.yml) roda os testes e monta a imagem Docker.

## Como as pastas estão organizadas

```
painel-demografico-brasil/
├── app.py                    # monta a tela: cabeçalho, números, controles, mapa e abas
├── src/
│   ├── dados.py              # todas as contas (DuckDB). É o único arquivo que lê data/ e geo/
│   ├── indicadores.py        # nome, cor, casas decimais e explicação de cada indicador; os temas
│   ├── graficos.py           # pirâmide com dois anos, grupos de idade, dependência e a frase do bônus
│   ├── estilo.py             # cabeçalho, números de destaque e rodapé
│   └── theme/                # o visual comum dos painéis Cenários (cores, cartões, CSS)
├── data/
│   ├── pop_ibge.parquet            # população por município, ano, sexo e idade
│   ├── ibge_ufs.parquet            # os 27 estados: código, sigla e nome
│   ├── nascimentos.parquet         # nascidos vivos por município, ano e idade da mãe (SINASC)
│   └── esperanca_vida_uf.parquet   # esperança de vida por estado e ano (IBGE)
├── geo/                      # contorno dos municípios e dos estados, para o mapa
├── scripts/
│   └── preparar_nascimentos.py     # baixa o SINASC e gera data/nascimentos.parquet
├── tests/                    # os testes
├── assets/                   # a bandeira do cabeçalho
└── vendor/                   # o cenarios_core, em versão fixa
```

## Como citar e licença

Se usar o painel ou o código num trabalho, use o botão **"Cite this repository"** aqui no GitHub, que lê o [`CITATION.cff`](CITATION.cff).

O código é aberto, sob a licença [MIT](LICENSE): pode ser usado, copiado e adaptado, desde que o aviso de copyright do Projeto Cenários vá junto. A licença vale para o código. Os dados são do IBGE e do DATASUS, e seguem as regras dessas fontes.
