"use client";

import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

import type { ParadaResponse, PontoTuristico } from "@/types";

// Cores por modo de transporte — o próprio mapa demonstra o comportamento
// multimodal do CrossRec (a decisão andar-vs-carro trecho a trecho).
const CORES_MODO: Record<string, string> = {
  walk: "#2563eb", // azul — a pé
  drive: "#f97316", // laranja — carro
};

function iconeNumerado(numero: number) {
  return L.divIcon({
    html: `<div style="background:#111827;color:#fff;border-radius:9999px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:13px;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)">${numero}</div>`,
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function AjustarLimites({ pontos }: { pontos: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (pontos.length > 0) {
      map.fitBounds(pontos, { padding: [40, 40] });
    }
  }, [pontos, map]);
  return null;
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
      <div className="flex h-full items-center justify-center text-sm text-gray-500">
        Sem paradas para mostrar no mapa.
      </div>
    );
  }

  return (
    <MapContainer center={coordenadas[0]} zoom={13} scrollWheelZoom className="h-full w-full rounded-lg">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <AjustarLimites pontos={coordenadas} />

      {paradasComPonto.map((item, indice) => (
        <Marker
          key={item.parada.ponto_id}
          position={[item.ponto.latitude, item.ponto.longitude]}
          icon={iconeNumerado(indice + 1)}
        >
          <Tooltip direction="top" offset={[0, -14]}>
            <strong>
              {indice + 1}. {item.ponto.nome}
            </strong>
            <br />
            {item.parada.hora_inicio_visita} – {item.parada.hora_fim_visita}
          </Tooltip>
        </Marker>
      ))}

      {paradasComPonto.slice(1).map((item, indice) => {
        const anterior = paradasComPonto[indice];
        const cor = CORES_MODO[item.parada.modo_chegada ?? "walk"] ?? "#6b7280";
        return (
          <Polyline
            key={`trecho-${item.parada.ponto_id}`}
            positions={[
              [anterior.ponto.latitude, anterior.ponto.longitude],
              [item.ponto.latitude, item.ponto.longitude],
            ]}
            pathOptions={{ color: cor, weight: 4, opacity: 0.8 }}
          />
        );
      })}
    </MapContainer>
  );
}
