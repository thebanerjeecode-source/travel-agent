/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone is for Docker self-hosting only — Railway uses default Next.js output.
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" } : {}),
};

module.exports = nextConfig;
