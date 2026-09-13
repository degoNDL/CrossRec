"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import LinhaDoTempo from "@/components/LinhaDoTempo";
import SeletorPontos from "@/components/SeletorPontos";
import { buscarPontos, calcularRoteiro, ErroApi, interpretarPedido } from "@/lib/api";
import { DIA_SEMANA_LABEL, DIAS_SEMANA } from "@/types";
import type { PontoTuristico, RoteiroResponse } from "@/types";

const MapaRota = dynamic(() => import("@/components/MapaRota"), { ssr: false });

const campoClasse =
  "mt-1.5 block w-full rounded-lg border px-3 py-2 text-sm outline-none transition-colors";
const campoEstilo = { background: "var(--bg-elevated-2)", borderColor: "var(--border)", color: "var(--text)" };

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
        setErroInterpretar(
          "Não encontrei pontos do catálogo que combinem com esse pedido. Tente descrever de outro jeito ou escolha manualmente abaixo."
        );
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
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* Abertura */}
      <header className="relative overflow-hidden border-b" style={{ borderColor: "var(--border)" }}>
        <div className="bg-map-texture pointer-events-none absolute inset-0 opacity-[0.35]" />
        <div
          className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full opacity-20 blur-3xl"
          style={{ background: "var(--coral)", animation: "drift 14s ease-in-out infinite" }}
        />
        <div
          className="pointer-events-none absolute -bottom-10 right-0 h-80 w-80 rounded-full opacity-25 blur-3xl"
          style={{ background: "var(--teal)", animation: "drift 18s ease-in-out infinite reverse" }}
        />

        <div className="relative mx-auto max-w-5xl px-6 py-14 sm:px-8 sm:py-20">
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-4 text-sm font-medium tracking-wide"
            style={{ color: "var(--teal)" }}
          >
            Recife, um dia de cada vez
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.05 }}
            className="font-display text-5xl leading-[1.05] sm:text-7xl"
            style={{ color: "var(--text)" }}
          >
            Atravesse o Recife
            <br />
            <span style={{ color: "var(--coral)", fontStyle: "italic" }}>na ordem certa.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mt-6 max-w-xl text-lg"
            style={{ color: "var(--text-muted)" }}
          >
            Escolha os pontos que quer visitar. O CrossRec decide a melhor ordem, quando ir a pé
            e quando ir de carro, e monta a linha do tempo do seu dia — respeitando o horário de
            cada lugar.
          </motion.p>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-12 sm:px-8">
        <section
          className="rounded-2xl border p-5"
          style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
        >
          <label htmlFor="texto-livre" className="mb-2 block text-sm font-medium" style={{ color: "var(--text-muted)" }}>
            Descreva o que você quer ver
          </label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              id="texto-livre"
              type="text"
              value={textoLivre}
              onChange={(e) => setTextoLivre(e.target.value)}
              placeholder='"quero ver o centro histórico e terminar numa praia"'
              className={campoClasse + " mt-0"}
              style={campoEstilo}
            />
            <button
              type="button"
              onClick={handleInterpretar}
              disabled={interpretando || textoLivre.trim().length < 3}
              className="shrink-0 rounded-lg px-4 py-2 text-sm font-semibold transition-opacity disabled:opacity-40"
              style={{ background: "var(--teal)", color: "#04241d" }}
            >
              {interpretando ? "Pensando…" : "Sugerir pontos"}
            </button>
          </div>
          {erroInterpretar && (
            <p className="mt-2 text-sm" style={{ color: "var(--gold)" }}>
              {erroInterpretar}
            </p>
          )}
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <div
            className="rounded-2xl border p-5"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <h2 className="font-display mb-3 text-xl" style={{ color: "var(--text)" }}>
              Pontos turísticos
            </h2>
            {carregandoCatalogo && <p className="text-sm" style={{ color: "var(--text-faint)" }}>Carregando catálogo…</p>}
            {erroCatalogo && (
              <p className="text-sm" style={{ color: "var(--coral)" }}>
                {erroCatalogo} — verifique se a API está rodando em{" "}
                {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}.
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

          <div
            className="flex flex-col gap-4 rounded-2xl border p-5"
            style={{ background: "var(--bg-elevated)", borderColor: "var(--border)" }}
          >
            <h2 className="font-display text-xl" style={{ color: "var(--text)" }}>
              Configurações do dia
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm" style={{ color: "var(--text-muted)" }}>
                Dia da semana
                <select
                  value={diaSemana}
                  onChange={(e) => setDiaSemana(e.target.value)}
                  className={campoClasse}
                  style={campoEstilo}
                >
                  {DIAS_SEMANA.map((dia) => (
                    <option key={dia} value={dia}>
                      {DIA_SEMANA_LABEL[dia]}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm" style={{ color: "var(--text-muted)" }}>
                Início (opcional)
                <select
                  value={pontoInicioId}
                  onChange={(e) => setPontoInicioId(e.target.value)}
                  className={campoClasse}
                  style={campoEstilo}
                >
                  <option value="">Melhor início automático</option>
                  {selecionados.map((id) => (
                    <option key={id} value={id}>
                      {catalogoPorId[id]?.nome ?? id}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm" style={{ color: "var(--text-muted)" }}>
                Início do dia
                <input
                  type="time"
                  value={horaInicio}
                  onChange={(e) => setHoraInicio(e.target.value)}
                  className={campoClasse}
                  style={campoEstilo}
                />
              </label>

              <label className="text-sm" style={{ color: "var(--text-muted)" }}>
                Fim do dia
                <input
                  type="time"
                  value={horaFim}
                  onChange={(e) => setHoraFim(e.target.value)}
                  className={campoClasse}
                  style={campoEstilo}
                />
              </label>
            </div>

            <label className="flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
              <input type="checkbox" checked={narrar} onChange={(e) => setNarrar(e.target.checked)} />
              Narrar o roteiro com IA (dicas por parada + sugestão de almoço)
            </label>

            <button
              type="button"
              onClick={handleCalcular}
              disabled={selecionados.length === 0 || calculando}
              className="mt-auto rounded-lg px-4 py-3 text-sm font-semibold transition-opacity disabled:opacity-40"
              style={{ background: "var(--coral)", color: "#2a0d03" }}
            >
              {calculando ? "Calculando…" : `Calcular roteiro (${selecionados.length} pontos)`}
            </button>
            {erroRoteiro && (
              <p className="text-sm" style={{ color: "var(--coral)" }}>
                {erroRoteiro}
              </p>
            )}
          </div>
        </section>

        <AnimatePresence>
          {roteiro && (
            <motion.section
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="flex flex-col gap-5 border-t pt-8"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-display text-2xl" style={{ color: "var(--text)" }}>
                  Seu roteiro
                </h2>
                <span className="text-sm" style={{ color: "var(--text-faint)" }}>
                  {Math.round(roteiro.custo_total_minutos)} min de deslocamento + espera
                </span>
              </div>

              {!roteiro.completo && (
                <div
                  className="rounded-lg px-4 py-3 text-sm"
                  style={{ background: "rgba(242,184,75,0.12)", color: "var(--gold)" }}
                >
                  Nem todos os pontos pedidos couberam no dia — selecionamos o melhor subconjunto
                  possível ({roteiro.paradas.length} de {selecionados.length} pontos).
                </div>
              )}

              {roteiro.pontos_ignorados_fechados.length > 0 && (
                <div
                  className="rounded-lg px-4 py-3 text-sm"
                  style={{ background: "var(--bg-elevated-2)", color: "var(--text-muted)" }}
                >
                  Fechado(s) em {DIA_SEMANA_LABEL[diaSemana]}, não entraram no cálculo:{" "}
                  {roteiro.pontos_ignorados_fechados.map((id) => catalogoPorId[id]?.nome ?? id).join(", ")}
                </div>
              )}

              <div className="grid gap-6 md:grid-cols-2">
                <div
                  className="h-[440px] overflow-hidden rounded-2xl border"
                  style={{ borderColor: "var(--border)" }}
                >
                  <MapaRota paradas={roteiro.paradas} catalogoPorId={catalogoPorId} />
                </div>
                <div className="overflow-y-auto md:max-h-[440px]">
                  <LinhaDoTempo paradas={roteiro.paradas} />
                </div>
              </div>

              <div className="flex gap-4 text-xs" style={{ color: "var(--text-faint)" }}>
                <span className="flex items-center gap-1.5">
                  <span className="inline-block h-2 w-4 rounded-full" style={{ background: "var(--teal)" }} /> a pé
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="inline-block h-2 w-4 rounded-full" style={{ background: "var(--coral)" }} /> de carro
                </span>
              </div>

              {roteiro.narrativa && (
                <div className="rounded-2xl p-6" style={{ background: "var(--bg-elevated)" }}>
                  <h3 className="font-display mb-3 text-xl italic" style={{ color: "var(--coral)" }}>
                    Seu dia no Recife
                  </h3>
                  <p
                    className="whitespace-pre-line text-[15px] leading-relaxed"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {roteiro.narrativa}
                  </p>
                </div>
              )}
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      <footer className="border-t px-6 py-8 text-center text-xs sm:px-8" style={{ borderColor: "var(--border)", color: "var(--text-faint)" }}>
        CrossRec — TSP multimodal do Recife, resolvido por Held-Karp exato + meta-heurística.
      </footer>
    </div>
  );
}
