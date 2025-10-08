import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8000/api/schema/",
  output: "src/services/django",
  plugins: [
    {
      name: "@hey-api/client-fetch",
      throwOnError: true,
    },
  ],
});
