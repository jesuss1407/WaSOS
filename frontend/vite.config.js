import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// data/ (raíz del repo) es la fuente de verdad de distritos y zonas críticas
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
})
