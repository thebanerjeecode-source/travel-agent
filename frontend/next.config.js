/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone is for Docker self-hosting only — Vercel uses its own output.
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" } : {}),
};

module.exports = nextConfig;
