# TRAMES — Programação Dinâmica

Algoritmo acadêmico em Python para buscar, classificar e recalcular percursos urbanos utilizando a base JSON exportada pela etapa de Data Science do projeto Trames.

## Integrantes

- Giovanna Oliveira Ferreira Dias - RM566647
- Maria Laura Pereira Druzeic - RM566634
- Marianne Mukai Nishikawa - RM568001
## Objetivo

O Trames propõe percursos urbanos que considerem características além da distância. Nesta entrega, o algoritmo utiliza o custo de recomendação produzido pela Engenharia de Features para comparar caminhos e apresenta o Índice de Adequação da Rota (IAR) e os scores associados aos trechos.

Este módulo é executado no terminal. Não inclui a interface do aplicativo, mapas ou navegação por GPS.

## Arquivos

| Arquivo | Descrição |
| --- | --- |
| `trames.py` | Código de leitura, validação, busca, classificação e recálculo. |
| `trames_base_integracao.json` | Base de trechos exportada por Data Science. |
| `README.md` | Documentação e instruções de execução. |

O código Python e o JSON devem estar na mesma pasta. Este README documenta a versão do código apresentada para o trabalho.

## Requisitos

- Python 3.
- Não é necessário instalar bibliotecas externas.
- Módulos utilizados: `json`, `math` e `functools`, disponíveis na biblioteca padrão.

## Como executar

1. Salve o código como `trames.py`.
2. Coloque `trames_base_integracao.json` na mesma pasta.
3. Abra o terminal nessa pasta.
4. Execute:

```bash
python trames.py
```

No Windows, se necessário, utilize:

```bash
py trames.py
```

O exemplo principal busca rotas do nó 1 ao nó 5. Depois, bloqueia o primeiro trecho da melhor opção e executa um recálculo.

Para alterar o percurso inicial, edite os parâmetros desta chamada:

```python
rotas = buscar_rotas(trechos, origem=1, destino=5)
```

## Dados de entrada

O arquivo JSON deve conter uma lista de objetos, cada um representando um trecho direcionado. Os campos utilizados pelo código são:

| Campo | Utilização |
| --- | --- |
| `id_trecho` | Identifica cada trecho de forma única. |
| `origem_id` | Identifica o nó de origem. |
| `destino_id` | Identifica o nó de destino. |
| `distancia_m` | Distância do trecho em metros. |
| `custo_recomendacao` | Peso utilizado na busca e classificação. |
| `IAR` | Indicador de adequação entre 0 e 100. |
| `score_recursos` | Score de recursos urbanos. |
| `score_seguranca` | Score relativo de segurança. |
| `score_avaliacao` | Score de avaliações. |

Outros campos da exportação, como penalidades, quantidades de ocorrências e confiança dos dados, permanecem no JSON, mas não são utilizados diretamente nesta versão do código.

O score de recursos não é interpretado como garantia de acessibilidade. Os IDs dos nós também não são tratados como coordenadas geográficas.

## Auditoria dos dados

A função `carregar_dados` verifica os registros antes da busca. Ela rejeita:

- Identificadores que não sejam inteiros positivos.
- IDs de trechos repetidos entre os registros aceitos.
- Distâncias zeradas, negativas, não numéricas ou não finitas.
- Custos negativos, não numéricos ou não finitos.
- IAR e scores fora do intervalo de 0 a 100.
- Ausência de campos obrigatórios ou incompatibilidades de tipo identificadas na validação.

Registros inválidos são ignorados com uma mensagem no terminal. Distâncias negativas não são convertidas para positivas, e valores ausentes não são substituídos silenciosamente por zero.

O conteúdo principal do JSON precisa ser uma lista. Arquivo ausente ou JSON com sintaxe incorreta gera uma exceção; esta versão não possui tratamento amigável para esses dois casos. Os campos adicionais da exportação não passam por auditoria completa nesta implementação.

## Modelagem dos caminhos

- Cada local corresponde a um nó.
- Cada trecho corresponde a uma conexão direcionada entre dois nós.
- O sentido `origem_id → destino_id` é respeitado.
- Trechos diferentes entre o mesmo par de nós são preservados pelo seu ID.
- Um caminho não pode visitar o mesmo nó duas vezes, evitando ciclos.

## Programação dinâmica com memoização

A função interna `resolver` utiliza `@lru_cache(maxsize=None)` para armazenar os resultados de subproblemas já calculados.

### Estado

Cada subproblema é identificado por:

```python
(atual, visitados)
```

`atual` é o nó em que a busca se encontra. `visitados` é um conjunto imutável dos nós já percorridos. O destino e os trechos disponíveis ficam fixos durante uma chamada de busca.

### Caso base

Ao alcançar o destino, a função retorna uma continuação vazia com custo zero.

### Transição

Para cada trecho disponível que leva a um nó ainda não visitado:

1. Resolve as melhores continuações a partir do próximo nó.
2. Soma o custo do trecho ao custo de cada continuação.
3. Acrescenta o ID do trecho ao caminho.
4. Ordena os candidatos e mantém as três melhores opções.

A memoização permite reutilizar as soluções quando o mesmo estado aparece novamente, em vez de repetir o cálculo.

### Reconstrução e classificação

Cada resultado armazena a sequência dos IDs dos trechos. Esses IDs permitem recuperar os registros e montar a sequência dos nós, a distância total e os indicadores agregados.

A classificação utiliza o menor custo acumulado. Em caso de empate, a sequência dos IDs dos trechos determina uma ordem estável. O programa retorna até três caminhos, conforme a disponibilidade.

## Custo e indicadores

O custo total de um caminho é:

```text
custo total = soma dos custos de recomendação dos trechos
```

O campo `custo_recomendacao` é consumido conforme exportado. O código não recalcula os pesos da Engenharia de Features nem soma novamente as penalidades, evitando possível dupla contagem.

Para exibição, o IAR e cada score da rota são calculados por média ponderada pela distância:

```text
indicador da rota = soma(indicador do trecho × distância do trecho)
                    ÷ distância total da rota
```

Essa agregação é uma regra do protótipo. O IAR não é somado entre trechos e não corresponde ao custo acumulado. A rota com menor custo não necessariamente terá o maior IAR médio.

A versão atual utiliza um único custo previamente calculado; não modifica os pesos conforme perfis escolhidos pelo usuário.

## Recálculo

A função `recalcular_rotas` recebe o local atual, o destino e os IDs dos trechos bloqueados. Ela chama novamente a busca, removendo esses trechos das opções disponíveis.

```python
novas_rotas = recalcular_rotas(
    trechos,
    local_atual=1,
    destino=5,
    bloqueados=[10]
)
```

Nesse exemplo, o trecho de ID 10 fica indisponível. A memória da busca é criada novamente em cada chamada, evitando o reaproveitamento de resultados anteriores ao bloqueio.

O bloqueio é informado manualmente. O programa não identifica obstáculos ou interdições automaticamente.

## Principais funções

| Função | Responsabilidade |
| --- | --- |
| `numero_valido` | Verificar se um número é finito e tem tipo válido. |
| `carregar_dados` | Ler o JSON e validar os campos utilizados. |
| `buscar_rotas` | Construir o grafo, resolver os subproblemas e classificar os caminhos. |
| `recalcular_rotas` | Executar uma nova busca com trechos bloqueados. |
| `mostrar_rotas` | Apresentar os resultados no terminal. |

## Saída

Para cada alternativa, o terminal apresenta:

- Posição na classificação.
- Sequência de nós e IDs dos trechos.
- Distância total em metros.
- Custo acumulado.
- IAR agregado.
- Scores agregados de recursos e segurança.

O score de avaliação também é calculado e incluído no resultado retornado por `buscar_rotas`, mas não é impresso pela função `mostrar_rotas` da versão apresentada.

Origem ou destino inexistente gera `ValueError`. Origem igual ao destino ou ausência de caminhos retorna uma lista vazia, acompanhada de uma mensagem geral na apresentação.

## Verificações sugeridas

Estes cenários devem ser executados e registrados pelo grupo; esta seção não afirma que os testes já foram realizados.

| Cenário | Comportamento esperado |
| --- | --- |
| Busca entre nós conectados | Retornar até três caminhos em ordem de custo. |
| Bloqueio do trecho recomendado | Recalcular sem utilizar o ID bloqueado. |
| Distância zero ou negativa | Ignorar o registro e emitir uma mensagem. |
| Score fora de 0 a 100 | Ignorar o registro e emitir uma mensagem. |
| Trechos paralelos | Preservar os registros com IDs diferentes. |
| Conexão em sentido único | Não criar automaticamente a conexão inversa. |
| Destino sem caminho | Retornar uma lista vazia. |
| Origem igual ao destino | Retornar uma lista vazia, sem deslocamento. |
| Empate de custo | Ordenar pelo critério determinístico dos IDs. |

## Complexidade e limitações

Para V nós, existem até V × 2^V combinações de nó atual e conjunto de visitados. Considerando E trechos e até três opções por estado, um limite superior conservador de tempo é O(2^V × E × (V + log E)), incluindo cópia de caminhos e ordenação de candidatos. O armazenamento dos caminhos em cache pode alcançar O(2^V × V²), além do grafo e das listas temporárias.

A solução é adequada a uma demonstração com poucos nós. O crescimento exponencial impede sua adoção direta para uma rede urbana grande.

Esta entrega não inclui seleção de perfis, localização em tempo real, mapa geográfico, API, identificação automática de barreiras ou garantia de segurança e acessibilidade. Esses recursos dependem de dados e implementações complementares.
