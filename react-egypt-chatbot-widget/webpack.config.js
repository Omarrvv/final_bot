const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const TerserPlugin = require("terser-webpack-plugin");

module.exports = (env, argv) => {
  const isProduction = argv.mode === "production";

  return {
    entry: "./src/widget.tsx",
    output: {
      path: path.resolve(__dirname, "build"),
      filename: isProduction
        ? "egypt-tourism-widget.min.js"
        : "egypt-tourism-widget.js",
      library: {
        name: "EgyptChatbot",
        type: "umd",
        export: "default",
      },
      globalObject: "this",
      clean: true,
    },
    module: {
      rules: [
        {
          test: /\.(ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
            options: {
              presets: [
                [
                  "@babel/preset-env",
                  {
                    targets: {
                      browsers: ["> 1%", "last 2 versions"],
                    },
                  },
                ],
                [
                  "@babel/preset-react",
                  {
                    runtime: "automatic",
                  },
                ],
                "@babel/preset-typescript",
              ],
            },
          },
        },
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
            options: {
              presets: [
                [
                  "@babel/preset-env",
                  {
                    targets: {
                      browsers: ["> 1%", "last 2 versions"],
                    },
                  },
                ],
                [
                  "@babel/preset-react",
                  {
                    runtime: "automatic",
                  },
                ],
              ],
            },
          },
        },
        {
          test: /\.css$/,
          use: [
            "style-loader",
            "css-loader",
            {
              loader: "postcss-loader",
              options: {
                postcssOptions: {
                  plugins: [require("tailwindcss"), require("autoprefixer")],
                },
              },
            },
          ],
        },
      ],
    },
    resolve: {
      extensions: [".tsx", ".ts", ".jsx", ".js"],
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: "./public/index.html",
        filename: "index.html",
        inject: "body",
      }),
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, "build"),
      },
      port: 8080,
      hot: true,
      open: true,
      historyApiFallback: true,
      allowedHosts: "all",
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods":
          "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        "Access-Control-Allow-Headers":
          "X-Requested-With, content-type, Authorization",
      },
    },
    optimization: {
      minimize: isProduction,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            compress: {
              drop_console: false, // Keep console.log for debugging
            },
          },
        }),
      ],
    },
    // Ensure React is bundled properly for UMD builds
    externals: isProduction ? {} : undefined,
  };
};
