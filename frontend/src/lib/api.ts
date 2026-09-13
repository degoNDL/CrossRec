import type {
  ApiErro,
  InterpretarResponse,
  PontoTuristico,
  RoteiroRequest,
  RoteiroResponse,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ErroApi extends Error {
  detalhes?: ApiErro;

  constructor(mensagem: string, detalhes?: ApiErro) {
    super(mensagem);
    this.name = "ErroApi";
    this.detalhes = detalhes;
  }
}

async function tratarResposta<T>(resposta: Response): Promise<T> {
  if (!resposta.ok) {
    let corpo: ApiErro | undefined;
    try {
      corpo = await resposta.json();
    } catch {
      // corpo de erro não era JSON — segue sem detalhes
    }
    throw new ErroApi(
      corpo?.detail ?? `Erro ${resposta.status} ao falar com a API do CrossRec.`,
      corpo
    );
  }
  return resposta.json();
}

export async function buscarPontos(): Promise<PontoTuristico[]> {
  const resposta = await fetch(`${API_URL}/pontos`);
  return tratarResposta<PontoTuristico[]>(resposta);
}

export async function calcularRoteiro(pedido: RoteiroRequest): Promise<RoteiroResponse> {
  const resposta = await fetch(`${API_URL}/roteiro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pedido),
  });
  return tratarResposta<RoteiroResponse>(resposta);
}

export async function interpretarPedido(texto: string): Promise<InterpretarResponse> {
  const resposta = await fetch(`${API_URL}/interpretar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  return tratarResposta<InterpretarResponse>(resposta);
}
