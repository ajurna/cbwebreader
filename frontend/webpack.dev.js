const path = require('path')
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker');
const webpack = require('webpack')

module.exports = (env = {}) => {
  return {

    mode: 'development',
    devtool: 'eval-cheap-source-map',
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
          use: [
            'style-loader',
            'css-loader'
          ]
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
        publicPath: 'http://localhost:8080/'
      }),
      new webpack.DefinePlugin({
        'process.env.BASE_URL': JSON.stringify(process.env.BASE_URL),
      }),
      new webpack.DefinePlugin({ __VUE_OPTIONS_API__: true, __VUE_PROD_DEVTOOLS__: true }),
    ],
    devServer: {
      headers: {
        "Access-Control-Allow-Origin":"*"
      },
      hot: true,
    }
  };
}