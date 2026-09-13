"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import LinhaDoTempo from "@/components/LinhaDoTempo";
import SeletorPontos from "@/components/SeletorPontos";
import { buscarPontos, calcularRoteiro, ErroApi, interpretarPedido } from "@/lib/api";
import { DIA_SEMANA_LABEL, DIAS_SEMANA } from "@/types";
import type { PontoTuristico, RoteiroResponse } from "@/types";

const MapaRota = dynamic(() => import("@/components/MapaRota"), { ssr: false });

export default function Home() {
  const [catalogo, setCatalogo] = useState<PontoTuristico[]>([]);
  const [carregandoCatalogo, setCarregandoCatalogo] = useState(true);
  const [erroCatalogo, setErroCatalogo] = useState<string | null>(null);

  const [selecionados, setSelecionados] = useState<string[]>([]);
  const [diaSemana, setDiaSemana] = useState("sabado");
  const [horaInicio, setHoraInicio] = useState("09:00");
  const [horaFim, setHoraFim] = useState("18:00");
  const [pontoInicioId, setPontoInicioId] = useState<string>("");
  const [narrar, setNarrar] = useState(false);

  const [textoLivre, setTextoLivre] = useState("");
  const [interpretando, setInterpretando] = useState(false);
  const [erroInterpretar, setErroInterpretar] = useState<string | null>(null);

  const [roteiro, setRoteiro] = useState<RoteiroResponse | null>(null);
  const [calculando, setCalculando] = useState(false);
  const [erroRoteiro, setErroRoteiro] = useState<string | null>(null);

  useEffect(() => {
    buscarPontos()
      .then(setCatalogo)
      .catch((e: unknown) =>
        setErroCatalogo(e instanceof Error ? e.message : "Erro ao carregar o catálogo de pontos.")
      )
      .finally(() => setCarregandoCatalogo(false));
  }, []);

  const catalogoPorId = useMemo(
    () => Object.fromEntries(catalogo.map((p) => [p.id, p])),
    [catalogo]
  );

  function adicionarPonto(id: string) {
    setSelecionados((atual) => (atual.includes(id) ? atual : [...atual, id]));
  }

  function removerPonto(id: string) {
    setSelecionados((atual) => atual.filter((pid) => pid !== id));
    if (pontoInicioId === id) setPontoInicioId("");
  }

  async function handleInterpretar() {
    if (textoLivre.trim().length < 3) return;
    setInterpretando(true);
    setErroInterpretar(null);
    try {
      const resultado = await interpretarPedido(textoLivre);
      if (resultado.pontos_ids.length === 0) {
        setErroInterpretar("Não encontrei pontos do catálogo que combinem com esse pedido. Tente descrever de outro jeito ou escolha manualmente abaixo.");
      }
      setSelecionados((atual) => [
        ...atual,
        ...resultado.pontos_ids.filter((id) => !atual.includes(id)),
      ]);
    } catch (e) {
      setErroInterpretar(e instanceof ErroApi ? e.message : "Erro ao interpretar o pedido.");
    } finally {
      setInterpretando(false);
    }
  }

  async function handleCalcular() {
    setCalculando(true);
    setErroRoteiro(null);
    setRoteiro(null);
    try {
      const resultado = await calcularRoteiro({
        pontos_ids: selecionados,
        dia_semana: diaSemana,
        hora_inicio_dia: horaInicio,
        hora_fim_dia: horaFim,
        ponto_inicio_id: pontoInicioId || null,
        narrar,
      });
      setRoteiro(resultado);
    } catch (e) {
      setErroRoteiro(e instanceof ErroApi ? e.message : "Erro ao calcular o roteiro.");
    } finally {
      setCalculando(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-8 sm:px-8">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">CrossRec</h1>
        <p className="text-gray-600">Otimizador multimodal de rotas turísticas para o Recife.</p>
      </header>

      <section className="rounded-lg border border-gray-200 p-4">
        <label htmlFor="texto-livre" className="mb-1 block text-sm font-medium text-gray-700">
          Descreva o que você quer ver (opcional)
        </label>
        <div className="flex gap-2">
          <input
            id="texto-livre"
            type="text"
            value={textoLivre}
            onChange={(e) => setTextoLivre(e.target.value)}
            placeholder='Ex: "quero ver o centro histórico e terminar numa praia"'
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-900 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleInterpretar}
            disabled={interpretando || textoLivre.trim().length < 3}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {interpretando ? "Pensando..." : "Sugerir pontos"}
          </button>
        </div>
        {erroInterpretar && <p className="mt-2 text-sm text-amber-700">{erroInterpretar}</p>}
      </section>

      <section className="grid items-start gap-6 md:grid-cols-2">
        <div>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Pontos turísticos</h2>
          {carregandoCatalogo && <p className="text-sm text-gray-500">Carregando catálogo...</p>}
          {erroCatalogo && (
            <p className="text-sm text-red-600">
              {erroCatalogo} — verifique se a API está rodando em {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
            </p>
          )}
          {!carregandoCatalogo && !erroCatalogo && (
            <SeletorPontos
              catalogo={catalogo}
              selecionados={selecionados}
              onAdicionar={adicionarPonto}
              onRemover={removerPonto}
            />
          )}
        </div>

        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-900">Configurações do dia</h2>

          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">
              Dia da semana
              <select
                value={diaSemana}
                onChange={(e) => setDiaSemana(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5"
              >
                {DIAS_SEMANA.map((dia) => (
                  <option key={dia} value={dia}>
                    {DIA_SEMANA_LABEL[dia]}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm">
              Ponto de início (opcional)
              <select
                value={pontoInicioId}
                onChange={(e) => setPontoInicioId(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5"
              >
                <option value="">Melhor início automático</option>
                {selecionados.map((id) => (
                  <option key={id} value={id}>
                    {catalogoPorId[id]?.nome ?? id}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm">
              Início do dia
              <input
                type="time"
                value={horaInicio}
                onChange={(e) => setHoraInicio(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5"
              />
            </label>

            <label className="text-sm">
              Fim do dia
              <input
                type="time"
                value={horaFim}
                onChange={(e) => setHoraFim(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-2 py-1.5"
              />
            </label>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={narrar} onChange={(e) => setNarrar(e.target.checked)} />
            Narrar o roteiro com IA (dicas por parada + sugestão de almoço)
          </label>

          <button
            type="button"
            onClick={handleCalcular}
            disabled={selecionados.length === 0 || calculando}
            className="rounded-md bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
          >
            {calculando ? "Calculando..." : `Calcular roteiro (${selecionados.length} pontos)`}
          </button>
          {erroRoteiro && <p className="text-sm text-red-600">{erroRoteiro}</p>}
        </div>
      </section>

      {roteiro && (
        <section className="flex flex-col gap-4 border-t border-gray-200 pt-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-gray-900">Seu roteiro</h2>
            <span className="text-sm text-gray-500">
              {Math.round(roteiro.custo_total_minutos)} min de deslocamento + espera
            </span>
          </div>

          {!roteiro.completo && (
            <div className="rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Nem todos os pontos pedidos coube no dia — selecionamos o melhor subconjunto possível
              ({roteiro.paradas.length} de {selecionados.length} pontos).
            </div>
          )}

          {roteiro.pontos_ignorados_fechados.length > 0 && (
            <div className="rounded-md bg-gray-100 px-4 py-3 text-sm text-gray-700">
              Fechado(s) em {DIA_SEMANA_LABEL[diaSemana]}, não entraram no cálculo:{" "}
              {roteiro.pontos_ignorados_fechados
                .map((id) => catalogoPorId[id]?.nome ?? id)
                .join(", ")}
            </div>
          )}

          <div className="grid gap-6 md:grid-cols-2">
            <div className="h-[420px] overflow-hidden rounded-lg border border-gray-200">
              <MapaRota paradas={roteiro.paradas} catalogoPorId={catalogoPorId} />
            </div>
            <div className="overflow-y-auto md:max-h-[420px]">
              <LinhaDoTempo paradas={roteiro.paradas} />
            </div>
          </div>

          <div className="flex gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-4 rounded bg-blue-600" /> a pé
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-4 rounded bg-orange-500" /> de carro
            </span>
          </div>

          {roteiro.narrativa && (
            <div className="rounded-lg bg-gray-50 p-4">
              <h3 className="mb-2 font-semibold text-gray-900">Seu dia no Recife</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700">
                {roteiro.narrativa}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
