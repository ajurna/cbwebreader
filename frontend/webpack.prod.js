const path = require('path')
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

const webpack = require('webpack')


module.exports = (env = {}) => {
  env.prod = true
  return {

    mode: 'production',
    devtool: 'hidden-source-map',
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
          test: /\.ts$/,
          loader: 'ts-loader',
          options: {
            appendTsSuffixTo: [/\.vue$/],
            transpileOnly: true
          }
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
        filename: './webpack-stats.json',
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
