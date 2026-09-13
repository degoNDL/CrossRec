import type { ParadaResponse } from "@/types";

const ROTULO_MODO: Record<string, string> = {
  walk: "🚶 a pé",
  drive: "🚗 de carro",
};

interface Props {
  paradas: ParadaResponse[];
}

export default function LinhaDoTempo({ paradas }: Props) {
  return (
    <ol className="flex flex-col gap-0">
      {paradas.map((parada, indice) => (
        <li key={parada.ponto_id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white">
              {indice + 1}
            </div>
            {indice < paradas.length - 1 && <div className="w-px flex-1 bg-gray-300" />}
          </div>
          <div className="pb-5">
            <p className="font-medium text-gray-900">{parada.nome}</p>
            <p className="text-sm text-gray-500">
              {parada.modo_chegada && (
                <>
                  chegada {ROTULO_MODO[parada.modo_chegada] ?? parada.modo_chegada} às{" "}
                  {parada.hora_chegada}
                  {parada.espera_minutos > 0 && (
                    <> (espera {Math.round(parada.espera_minutos)} min)</>
                  )}
                  {" · "}
                </>
              )}
              visita das {parada.hora_inicio_visita} às {parada.hora_fim_visita}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
