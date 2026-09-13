"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

import type { ParadaResponse, PontoTuristico } from "@/types";

// Cores por modo de transporte — o próprio mapa demonstra o comportamento
// multimodal do CrossRec (a decisão andar-vs-carro trecho a trecho).
const CORES_MODO: Record<string, string> = {
  walk: "#2bd9c2",
  drive: "#ff6b47",
};

function iconeNumerado(numero: number, ehInicio: boolean, delayMs: number) {
  const cor = ehInicio ? "#ff6b47" : "#0a141c";
  const corTexto = ehInicio ? "#1a0a05" : "#f6f1e7";
  const borda = ehInicio ? "#ffb499" : "#2bd9c2";
  return L.divIcon({
    html: `<div style="animation: marker-pop 480ms cubic-bezier(.34,1.56,.64,1) ${delayMs}ms backwards; background:${cor};color:${corTexto};border-radius:9999px;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;font-family:var(--font-sans);border:2px solid ${borda};box-shadow:0 2px 10px rgba(0,0,0,.45)">${numero}</div>`,
    className: "",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

function AjustarLimites({ pontos }: { pontos: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (pontos.length > 0) {
      map.fitBounds(pontos, { padding: [48, 48] });
    }
  }, [pontos, map]);
  return null;
}

function TrechoAnimado({
  id,
  positions,
  color,
  delayMs,
}: {
  id: string;
  positions: [number, number][];
  color: string;
  delayMs: number;
}) {
  const ref = useRef<L.Polyline>(null);

  useEffect(() => {
    const layer = ref.current;
    // `_path` é o nó SVG interno do Leaflet para layers de Path (não é API
    // pública documentada, mas é o jeito padrão de animar traçado no
    // ecossistema react-leaflet — sem isso teríamos que reimplementar o
    // renderer de polyline do zero só para medir o comprimento do traço).
    const path = (layer as unknown as { _path?: SVGPathElement } | null)?._path;
    if (!path) return;

    const length = path.getTotalLength();
    path.style.transition = "none";
    path.style.strokeDasharray = `${length}`;
    path.style.strokeDashoffset = `${length}`;
    const frame = requestAnimationFrame(() => {
      path.style.transition = `stroke-dashoffset 850ms cubic-bezier(.4,0,.2,1) ${delayMs}ms`;
      path.style.strokeDashoffset = "0";
    });
    return () => cancelAnimationFrame(frame);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <Polyline ref={ref} positions={positions} pathOptions={{ color, weight: 4, opacity: 0.85 }} />
  );
}

interface Props {
  paradas: ParadaResponse[];
  catalogoPorId: Record<string, PontoTuristico>;
}

export default function MapaRota({ paradas, catalogoPorId }: Props) {
  const paradasComPonto = paradas
    .map((parada) => ({ parada, ponto: catalogoPorId[parada.ponto_id] }))
    .filter((item): item is { parada: ParadaResponse; ponto: PontoTuristico } => Boolean(item.ponto));

  const coordenadas: [number, number][] = paradasComPonto.map((item) => [
    item.ponto.latitude,
    item.ponto.longitude,
  ]);

  if (coordenadas.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-[var(--text-muted)]">
        Sem paradas para mostrar no mapa.
      </div>
    );
  }

  return (
    <MapContainer center={coordenadas[0]} zoom={13} scrollWheelZoom className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <AjustarLimites pontos={coordenadas} />

      {paradasComPonto.slice(1).map((item, indice) => {
        const anterior = paradasComPonto[indice];
        const cor = CORES_MODO[item.parada.modo_chegada ?? "walk"] ?? "#6b7280";
        return (
          <TrechoAnimado
            key={`trecho-${item.parada.ponto_id}`}
            id={item.parada.ponto_id}
            positions={[
              [anterior.ponto.latitude, anterior.ponto.longitude],
              [item.ponto.latitude, item.ponto.longitude],
            ]}
            color={cor}
            delayMs={indice * 260}
          />
        );
      })}

      {paradasComPonto.map((item, indice) => (
        <Marker
          key={item.parada.ponto_id}
          position={[item.ponto.latitude, item.ponto.longitude]}
          icon={iconeNumerado(indice + 1, indice === 0, indice * 260)}
        >
          <Tooltip direction="top" offset={[0, -16]}>
            <strong>
              {indice + 1}. {item.ponto.nome}
            </strong>
            <br />
            {item.parada.hora_inicio_visita} – {item.parada.hora_fim_visita}
          </Tooltip>
        </Marker>
      ))}
    </MapContainer>
  );
}
