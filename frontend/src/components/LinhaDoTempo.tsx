"use client";

import { motion } from "framer-motion";

import type { ParadaResponse } from "@/types";

const ROTULO_MODO: Record<string, string> = {
  walk: "a pé",
  drive: "de carro",
};

const COR_MODO: Record<string, string> = {
  walk: "var(--teal)",
  drive: "var(--coral)",
};

interface Props {
  paradas: ParadaResponse[];
}

export default function LinhaDoTempo({ paradas }: Props) {
  return (
    <ol className="flex flex-col gap-0">
      {paradas.map((parada, indice) => (
        <motion.li
          key={parada.ponto_id}
          className="flex gap-4"
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: indice * 0.09, ease: "easeOut" }}
        >
          <div className="flex flex-col items-center">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
              style={{
                background: indice === 0 ? "var(--coral)" : "var(--bg-elevated-2)",
                color: indice === 0 ? "#1a0a05" : "var(--text)",
                border: `2px solid ${indice === 0 ? "#ffb499" : "var(--teal)"}`,
              }}
            >
              {indice + 1}
            </div>
            {indice < paradas.length - 1 && (
              <div className="w-px flex-1" style={{ background: "var(--border-strong)" }} />
            )}
          </div>
          <div className="pb-6">
            <p className="font-display text-lg" style={{ color: "var(--text)" }}>
              {parada.nome}
            </p>
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              {parada.modo_chegada && (
                <>
                  <span style={{ color: COR_MODO[parada.modo_chegada] }}>
                    chegada {ROTULO_MODO[parada.modo_chegada] ?? parada.modo_chegada}
                  </span>{" "}
                  às {parada.hora_chegada}
                  {parada.espera_minutos > 0 && (
                    <> · espera {Math.round(parada.espera_minutos)} min</>
                  )}
                  {" · "}
                </>
              )}
              visita das {parada.hora_inicio_visita} às {parada.hora_fim_visita}
            </p>
          </div>
        </motion.li>
      ))}
    </ol>
  );
}
