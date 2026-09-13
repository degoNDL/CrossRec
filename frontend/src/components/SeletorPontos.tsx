"use client";

import { useMemo, useState } from "react";

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
    <div className="flex flex-col gap-3">
      <div>
        <label htmlFor="busca-pontos" className="mb-1 block text-sm font-medium text-gray-700">
          Buscar pontos turísticos
        </label>
        <input
          id="busca-pontos"
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Ex: museu, praia, mercado..."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
        />
      </div>

      {selecionados.length > 0 && (
        <div>
          <p className="mb-1 text-sm font-medium text-gray-700">
            Selecionados ({selecionados.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {selecionados.map((id) => (
              <span
                key={id}
                className="flex items-center gap-1.5 rounded-full bg-gray-900 py-1 pl-3 pr-2 text-xs text-white"
              >
                {catalogoPorId[id]?.nome ?? id}
                <button
                  type="button"
                  onClick={() => onRemover(id)}
                  aria-label={`Remover ${catalogoPorId[id]?.nome ?? id}`}
                  className="rounded-full px-1 hover:bg-white/20"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <ul className="flex max-h-72 flex-col gap-1 overflow-y-auto rounded-md border border-gray-200 p-1">
        {disponiveis.length === 0 && (
          <li className="px-3 py-4 text-center text-sm text-gray-400">Nenhum ponto encontrado.</li>
        )}
        {disponiveis.map((ponto) => (
          <li key={ponto.id}>
            <button
              type="button"
              onClick={() => onAdicionar(ponto.id)}
              className="flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm hover:bg-gray-100"
            >
              <span>
                {ponto.nome}
                <span className="ml-2 text-xs text-gray-400">{ponto.categoria}</span>
              </span>
              <span className="text-lg leading-none text-gray-400">+</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
