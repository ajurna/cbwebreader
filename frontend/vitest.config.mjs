import path from 'node:path'
import { fileURLToPath } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'src')

export default defineConfig({
  plugins: [vue()],
  // The source imports components without the .vue extension (e.g. '@/views/BrowseView'),
  // so mirror the extension list used by frontend/webpack.dev.js.
  resolve: { extensions: ['.ts', '.js', '.vue', '.json'] },
  test: {
    environment: 'jsdom',
    alias: { '@': SRC },
  },
})
