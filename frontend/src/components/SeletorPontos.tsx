"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import type { PontoTuristico } from "@/types";

interface Props {
  catalogo: PontoTuristico[];
  selecionados: string[];
  onAdicionar: (id: string) => void;
  onRemover: (id: string) => void;
}

export default function SeletorPontos({ catalogo, selecionados, onAdicionar, onRemover }: Props) {
  const [busca, setBusca] = useState("");

  const catalogoPorId = useMemo(
    () => Object.fromEntries(catalogo.map((p) => [p.id, p])),
    [catalogo]
  );

  const disponiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return catalogo.filter((p) => {
      if (selecionados.includes(p.id)) return false;
      if (!termo) return true;
      return p.nome.toLowerCase().includes(termo) || p.categoria.toLowerCase().includes(termo);
    });
  }, [catalogo, busca, selecionados]);

  return (
    <div className="flex flex-col gap-4">
      <div>
        <label htmlFor="busca-pontos" className="mb-1.5 block text-sm font-medium text-[var(--text-muted)]">
          Buscar pontos
        </label>
        <input
          id="busca-pontos"
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="museu, praia, mercado..."
          className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none transition-colors"
          style={{
            background: "var(--bg-elevated-2)",
            borderColor: "var(--border)",
            color: "var(--text)",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--coral)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        />
      </div>

      {selecionados.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--text-faint)]">
            Selecionados ({selecionados.length})
          </p>
          <div className="flex flex-wrap gap-2">
            <AnimatePresence initial={false}>
              {selecionados.map((id) => (
                <motion.span
                  key={id}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.85 }}
                  transition={{ duration: 0.18 }}
                  className="flex items-center gap-1.5 rounded-full py-1.5 pl-3.5 pr-2 text-xs font-medium"
                  style={{ background: "var(--coral-bg)", color: "#ffc9b5", border: "1px solid rgba(255,107,71,0.35)" }}
                >
                  {catalogoPorId[id]?.nome ?? id}
                  <button
                    type="button"
                    onClick={() => onRemover(id)}
                    aria-label={`Remover ${catalogoPorId[id]?.nome ?? id}`}
                    className="rounded-full px-1 leading-none hover:bg-white/10"
                  >
                    ×
                  </button>
                </motion.span>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      <ul
        className="flex max-h-72 flex-col gap-1 overflow-y-auto rounded-lg border p-1.5"
        style={{ borderColor: "var(--border)" }}
      >
        {disponiveis.length === 0 && (
          <li className="px-3 py-6 text-center text-sm text-[var(--text-faint)]">Nenhum ponto encontrado.</li>
        )}
        {disponiveis.map((ponto) => (
          <li key={ponto.id}>
            <button
              type="button"
              onClick={() => onAdicionar(ponto.id)}
              className="group flex w-full items-center justify-between rounded-md px-3 py-2.5 text-left text-sm transition-colors hover:bg-white/5"
            >
              <span style={{ color: "var(--text)" }}>
                {ponto.nome}
                <span className="ml-2 text-xs" style={{ color: "var(--text-faint)" }}>
                  {ponto.categoria}
                </span>
              </span>
              <span
                className="text-lg leading-none transition-colors group-hover:text-[var(--teal)]"
                style={{ color: "var(--text-faint)" }}
              >
                +
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
