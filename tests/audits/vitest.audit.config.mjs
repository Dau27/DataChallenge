import { fileURLToPath } from 'node:url';
const pathFromHere = value => fileURLToPath(new URL(value, import.meta.url));
export default {
  root: pathFromHere('../../frontend/'),
  esbuild: { jsx: 'automatic' },
  resolve: { alias: {
    react: pathFromHere('../../frontend/node_modules/react/'),
    'react-dom': pathFromHere('../../frontend/node_modules/react-dom/'),
    '@testing-library/react': pathFromHere('../../frontend/node_modules/@testing-library/react/dist/index.js'),
    vitest: pathFromHere('../../frontend/node_modules/vitest/dist/index.js'),
  } },
  test: { include: ['../tests/audits/technical_freshness.audit.test.tsx'], environment: 'happy-dom', fileParallelism: false },
};
