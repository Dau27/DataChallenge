import { spawnSync } from 'node:child_process';
const result = spawnSync(process.execPath, ['node_modules/vitest/vitest.mjs', 'run', '--config', 'vitest.live.config.ts'], {
  stdio: 'inherit', env: { ...process.env, CQA_LIVE_SMOKE: '1' },
});
process.exit(result.status ?? 1);
