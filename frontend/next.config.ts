import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // Permite usar <Image> do Next com imagens hospedadas no R2.
  // Se mudar o domínio do R2, atualize aqui.
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "pub-cca907e05b984c7e8a17adec22c1bd44.r2.dev",
      },
    ],
  },
};

export default nextConfig;
