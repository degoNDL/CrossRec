# data/

Pipeline de dados dos pontos turísticos do Recife (Fase 1).

## Arquivos

- `schema.py` — modelo Pydantic `TouristPoint`, o formato canônico de um ponto.
- `collect_overpass.py` — coleta bruta via Overpass API (OSM). Gera `raw/osm_points.json`.
  Serve como base exploratória e para cross-check de coordenadas, **não** é a fonte de
  verdade do MVP (cobertura e qualidade do OSM variam muito).
- `curated_points.json` — dataset curado manualmente: 15-20 pontos-âncora conhecidos do
  Recife, com horário de funcionamento validado contra fonte oficial. **Esta é a fonte de
  verdade usada pelo otimizador.**
- `validate_points.py` — valida `curated_points.json` contra o schema e contra regras de
  sanidade (coordenadas dentro do bbox do Recife, ids únicos, horário presente etc.).

## Por que curadoria manual em vez de só OSM?

O OSM frequentemente tem `opening_hours` desatualizado ou ausente. Como o otimizador
descarta rotas que chegam fora do horário de funcionamento, um horário errado gera rotas
impossíveis ou perde soluções válidas. Por isso cada ponto do `curated_points.json` tem
o campo `fonte`, apontando para onde o horário foi confirmado (site oficial, Prefeitura
do Recife etc.), e `observacoes` quando algo não pôde ser confirmado com confiança.

## Rodando

```bash
python -m data.collect_overpass   # coleta bruta (opcional, exploratório)
python -m data.validate_points    # valida o dataset curado
```

## Pontos pesquisados mas deixados de fora do MVP

Durante a curadoria, 2 pontos populares do Recife (Basílica e Convento do Carmo, e
Catedral/Concatedral de São Pedro dos Clérigos) não tiveram horário de funcionamento
confirmável em fonte oficial — as fontes disponíveis divergiam entre si e não havia
página oficial acessível com horário de visitação (só de missas). Em vez de inventar um
horário, eles ficaram de fora de `curated_points.json` por enquanto. Para adicioná-los:
confirmar horário por telefone/Instagram oficial e então incluir seguindo o schema em
`schema.py`.

- Basílica e Convento do Carmo — tel. (81) 3224-3341
- Concatedral São Pedro dos Clérigos — Instagram @concatedralsaopedrodosclerigos

## Grafo de ruas e velocidade viária (Fase 2)

`graph.py` baixa (via OSMnx) e cacheia em `cache/` duas redes de ruas do Recife: uma de
caminhada e uma de carro. A rede de carro precisa de velocidade por via para estimar
tempo de deslocamento; investigamos o portal de dados abertos do Recife
(dados.recife.pe.gov.br) e ele **não tem** um dataset de limite de velocidade por
segmento de via — só tem contagem de veículos por faixa de velocidade em pontos fixos
de radar/lombada (dataset "Velocidade das Vias", mantido pela CTTU), que cobre apenas os
cruzamentos monitorados, não a malha completa. Cruzar esse dataset por trecho de rua
seria um esforço grande para um ganho de precisão pequeno no MVP.

Por isso `graph.py` usa a tag `maxspeed` do OSM quando existe e, onde falta (a maioria
das vias locais), imputa por uma tabela de velocidade por classe viária baseada no
Código de Trânsito Brasileiro (Art. 61): via de trânsito rápido 80 km/h, arterial 60,
coletora 40, local 30. Ver `HWY_SPEEDS_KMH` em `graph.py`.

Possível refinamento futuro (Fase 9): cruzar o dataset de velocidade da CTTU
(dados.recife.pe.gov.br/dataset/velocidade-das-vias-quantitativo-por-velocidade-media-2022)
com o dataset de localização dos equipamentos
(dados.recife.pe.gov.br/dataset/equipamentos-de-monitoramento-e-fiscalizacao-de-transito)
para calibrar as velocidades por classe viária com dado real observado, em vez de só a
tabela do CTB.
