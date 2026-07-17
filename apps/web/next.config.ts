import type { NextConfig } from "next";

const basePath =
  process.env.GITHUB_PAGES === "true" ? "/PhD-Opportunity-Tracker" : "";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath,
  images: {
    unoptimized: true,
  },
  experimental: {
    typedRoutes: true,
  },
};

export default nextConfig;
