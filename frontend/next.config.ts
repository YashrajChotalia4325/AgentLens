import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a small self-contained server in .next/standalone, used by the Dockerfile.
  output: "standalone",
};

export default nextConfig;
