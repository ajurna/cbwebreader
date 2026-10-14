const path = require('path')
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const webpack = require('webpack')


module.exports = (env = {}) => {
  env.prod = true
  return {

    mode: 'production',
    // No source maps in production: they are not served to browsers, but collectstatic
    // copies them into /static/ so browser devtools would pull ~3.3 MiB of maps.
    devtool: false,
    entry: path.resolve(__dirname, './src/main.js'),
    output: {
      path: path.resolve(__dirname, './dist/bundles/'),
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          use: 'vue-loader'
        },
        {
          test: /\.css$/,
          use: [MiniCssExtractPlugin.loader, "css-loader"],
        }
      ]
    },
    resolve: {
      extensions: ['.ts', '.js', '.vue', '.json'],
      alias: {
        'vue': '@vue/runtime-dom',
        '@': path.resolve('src'),
      }
    },
    plugins: [
      new VueLoaderPlugin(),
      new BundleTracker({
        filename: 'webpack-stats.json',
        path: path.resolve(__dirname, './'),
        publicPath: '/static/bundles/',
        integrity: true
      }),
      new webpack.DefinePlugin({
        'process.env.BASE_URL': JSON.stringify(process.env.BASE_URL),
      }),
      new webpack.DefinePlugin({ __VUE_OPTIONS_API__: true, __VUE_PROD_DEVTOOLS__: false }),
      new MiniCssExtractPlugin(),

      // new BundleAnalyzerPlugin(),
    ],
    optimization: {
      splitChunks: {
        chunks: 'all',
      },
    },
  };
}
