import pytest

from optimizer.cost import MODE_SWITCH_PENALTY_MINUTES, CostModel


@pytest.fixture
def cost_model():
    # Matrizes sintéticas — evita depender de download real do grafo do
    # Recife nos testes (lento e frágil em CI). A lógica de decisão de modo
    # é testada isoladamente aqui; o build real das matrizes é validado por
    # `optimizer/matrices.py` rodado manualmente (ver data/README.md).
    walk_matrix = {
        "perto-a": {"perto-a": 0.0, "perto-b": 5.0, "longe": 90.0},
        "perto-b": {"perto-a": 5.0, "perto-b": 0.0, "longe": 92.0},
        "longe": {"perto-a": 90.0, "perto-b": 92.0, "longe": 0.0},
    }
    drive_matrix = {
        "perto-a": {"perto-a": 0.0, "perto-b": 10.0, "longe": 12.0},
        "perto-b": {"perto-a": 10.0, "perto-b": 0.0, "longe": 11.0},
        "longe": {"perto-a": 12.0, "perto-b": 11.0, "longe": 0.0},
    }
    return CostModel(walk_matrix, drive_matrix)


def test_trecho_curto_prefere_caminhada(cost_model):
    resultado = cost_model.cost("perto-a", "perto-b")
    assert resultado.mode == "walk"
    assert resultado.minutes == 5.0


def test_trecho_longo_prefere_carro_mesmo_com_penalidade(cost_model):
    resultado = cost_model.cost("perto-a", "longe")
    assert resultado.mode == "drive"
    assert resultado.minutes == 12.0 + MODE_SWITCH_PENALTY_MINUTES


def test_mesmo_ponto_custa_zero(cost_model):
    resultado = cost_model.cost("perto-a", "perto-a")
    assert resultado.minutes == 0.0


def test_sem_caminho_a_pe_usa_carro():
    walk_matrix = {"a": {"a": 0.0, "b": None}, "b": {"a": None, "b": 0.0}}
    drive_matrix = {"a": {"a": 0.0, "b": 8.0}, "b": {"a": 8.0, "b": 0.0}}
    model = CostModel(walk_matrix, drive_matrix)

    resultado = model.cost("a", "b")
    assert resultado.mode == "drive"
    assert resultado.minutes == 8.0 + MODE_SWITCH_PENALTY_MINUTES


def test_sem_nenhum_caminho_levanta_erro():
    walk_matrix = {"a": {"a": 0.0, "b": None}, "b": {"a": None, "b": 0.0}}
    drive_matrix = {"a": {"a": 0.0, "b": None}, "b": {"a": None, "b": 0.0}}
    model = CostModel(walk_matrix, drive_matrix)

    with pytest.raises(ValueError):
        model.cost("a", "b")
