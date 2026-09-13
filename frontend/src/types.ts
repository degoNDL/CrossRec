export type Modo = "walk" | "drive";

export interface PontoTuristico {
  id: string;
  nome: string;
  endereco: string;
  latitude: number;
  longitude: number;
  categoria: string;
  horario_funcionamento: Record<string, string>;
  fecha_segunda: boolean;
  tempo_visita_sugerido_minutos: number;
  fonte?: string | null;
  observacoes?: string | null;
}

export interface RoteiroRequest {
  pontos_ids: string[];
  dia_semana: string;
  hora_inicio_dia?: string;
  hora_fim_dia?: string;
  ponto_inicio_id?: string | null;
  narrar?: boolean;
}

export interface ParadaResponse {
  ponto_id: string;
  nome: string;
  modo_chegada: Modo | null;
  hora_chegada: string;
  espera_minutos: number;
  hora_inicio_visita: string;
  hora_fim_visita: string;
}

export interface RoteiroResponse {
  completo: boolean;
  paradas: ParadaResponse[];
  pontos_ignorados_fechados: string[];
  custo_total_minutos: number;
  narrativa?: string | null;
}

export interface InterpretarResponse {
  pontos_ids: string[];
  pontos: PontoTuristico[];
}

export interface ApiErro {
  detail: string;
  erros?: { campo: string; mensagem: string }[];
}

export const DIAS_SEMANA = [
  "segunda",
  "terca",
  "quarta",
  "quinta",
  "sexta",
  "sabado",
  "domingo",
] as const;

export const DIA_SEMANA_LABEL: Record<string, string> = {
  segunda: "Segunda-feira",
  terca: "Terça-feira",
  quarta: "Quarta-feira",
  quinta: "Quinta-feira",
  sexta: "Sexta-feira",
  sabado: "Sábado",
  domingo: "Domingo",
};
