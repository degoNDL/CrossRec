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
