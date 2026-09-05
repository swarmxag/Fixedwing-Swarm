const { merge } = require('webpack-merge');
const baseConfig = require('./base.config.js');
const path = require('path');
const nodeExternals = require('webpack-node-externals');

const plugins = [];

module.exports = merge(baseConfig, {
  entry: './launcher.js',
  output: {
    filename: 'launcher.bundle.js',
  },
  // externals: [nodeExternals()],
  node: {
    __dirname: false,
    __filename: false,
  },

  plugins,

  target: 'electron-main',
});
