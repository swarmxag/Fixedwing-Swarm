/**
 * @file Empty configuration override, which preserves all the defaults.
 */

import { type ConfigOverrides } from 'config-overrides';

const overrides: ConfigOverrides = {
  // The bundled local server listens on port 5000 (Socket.IO/WebSocket),
  // not the generic default of 5001/TCP that the onboarding saga would
  // otherwise infer -- override it so the very first launch (and any
  // launch before the user has ever set a hostname manually) connects
  // to the right place and this triggers the local-server auto-launch.
  server: {
    port: 5000,
  },
};

export default overrides;
