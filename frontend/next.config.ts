import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Leaflet inicializa o mapa imperativamente no nó do DOM (`L.map(container)`)
  // e guarda estado nesse nó. O duplo-efeito do Strict Mode em dev (monta,
  // desmonta, monta de novo) faz o Leaflet achar que o container já está em
  // uso por outra instância. É incompatibilidade conhecida react-leaflet +
  // Strict Mode, não um bug do nosso código — e não afeta produção (o
  // duplo-efeito só roda em `next dev`).
  reactStrictMode: false,
  // Build "standalone" copia só o necessário para rodar (server.js + deps
  // usadas) — é o que permite uma imagem Docker enxuta em vez de levar o
  // node_modules inteiro. Sem efeito no deploy pela Vercel (que não usa
  // este Dockerfile, tem seu próprio pipeline nativo para Next.js).
  output: "standalone",
};

export default nextConfig;
