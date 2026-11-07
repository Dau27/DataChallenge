import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    include: ['src/live-workflow.test.tsx'],
    environment: 'happy-dom',
    environmentOptions: { happyDOM: { url: 'http://127.0.0.1:8000' } },
  },
});
