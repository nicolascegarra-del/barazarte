import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Genera un servidor mínimo autocontenido para la imagen Docker de producción.
  output: "standalone",
};

export default nextConfig;
