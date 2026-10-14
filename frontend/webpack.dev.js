const path = require('path')
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker');
const webpack = require('webpack')

// The dev server port. Keep this and the publicPath in sync - django-webpack-loader
// builds the script URL from the publicPath written into webpack-stats.json.
const DEV_PORT = process.env.DEV_PORT || 8001
const DEV_PUBLIC_PATH = `http://localhost:${DEV_PORT}/`

module.exports = () => {
  return {

    mode: 'development',
    devtool: 'eval-cheap-source-map',
    entry: path.resolve(__dirname, './src/main.js'),
    output: {
      path: path.resolve(__dirname, './dist/bundles/'),
      publicPath: DEV_PUBLIC_PATH,
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          use: 'vue-loader'
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
        filename: 'webpack-stats.json',
        path: path.resolve(__dirname, './'),
        publicPath: DEV_PUBLIC_PATH
      }),
      new webpack.DefinePlugin({
        'process.env.BASE_URL': JSON.stringify(process.env.BASE_URL),
      }),
      new webpack.DefinePlugin({ __VUE_OPTIONS_API__: true, __VUE_PROD_DEVTOOLS__: true }),
    ],
    devServer: {
      port: DEV_PORT,
      headers: {
        "Access-Control-Allow-Origin":"*"
      },
      hot: true,
    }
  };
}
