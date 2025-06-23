const { merge } = require("webpack-merge");
const commonConfig = require("./common.config");

// Use BACKEND_URL env variable or fallback to localhost:8000
const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

module.exports = merge(commonConfig, {
  mode: "development",
  devtool: "inline-source-map",
  devServer: {
    port: 3000,
    proxy: [
      {
        context: ["/"],
        target: backendUrl,
        changeOrigin: true,
      },
    ],
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
        runtimeErrors: true,
      },
    },
    hot: false,
    liveReload: true,
    allowedHosts: "all",
    host: "0.0.0.0",
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers":
        "X-Requested-With, content-type, Authorization",
    },
  },
  output: {
    publicPath: "/",
  },
});
