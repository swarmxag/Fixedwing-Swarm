/**
 * @file
 * Default values for the configuration options of the application.
 */

import { type Config } from 'config';

const skybrushIcon =
  'data:image/png;base64,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';

const defaults: Config = {
  branding: {
    splashIcon: skybrushIcon,
    splashTitle: 'XAG GCS',
  },

  ephemeral: false,

  examples: {
    shows: [],
  },

  features: {
    loadShowFromCloud: false,
    perspectives: false,
  },

  headerComponents: [
    ['uav-status-summary'],
    [
      'altitude-summary-header-button',
      'battery-status-header-button',
      'rtk-status-header-button',
    ],
    ['weather-header-button'],
    ['connection-status-button'],
    [
      'server-connection-settings-button',
      'geofence-settings-button',
      'authentication-button',
    ],
    [
      'broadcast-button',
      'toolbox-button',
      'app-settings-button',
      'alert-button',
      'help-button',
      'full-screen-button',
      'session-expiry-box',
    ],
  ],

  map: {
    drawingTools: [
      ['select', 'zoom'],
      [
        'add-marker',
        'draw-path',
        'draw-circle',
        'draw-rectangle',
        'draw-polygon',
        'cut-hole',
        'edit-feature',
      ],
    ],

    features: {
      onCreate() {
        /* do nothing */
      },
    },
  },

  optimizeForSingleUAV: {
    default: false,
    force: false,
  },

  optimizeUIForTouch: {
    default: null,
    force: false,
  },

  perspectives: ['default'],

  ribbon: {
    label: null,
    position: 'bottomRight',
  },

  server: {
    connectAutomatically: true,
    preventAutodetection: false,
    preventManualSetup: false,
    hostName: 'localhost',
    port: null,
    isSecure: null,
    warnClockSkew: true,
  },

  session: {
    maxLengthInSeconds: null,
  },

  toastPlacement: 'top-center',
  tour: null,

  urls: {
    help: 'https://doc.collmot.com/public/skybrush-live-doc/latest',
    exit: null,
  },
  strike_url: [
    {
      id: 1,
      url: 'http://192.168.6.151:8000/strike',
    },
    {
      id: 2,
      url: 'http://192.168.6.152:8000/strike',
    },
    {
      id: 3,
      url: 'http://192.168.6.153:8000/strike',
    },
    {
      id: 4,
      url: 'http://192.168.6.154:8000/strike',
    },
    {
      id: 5,
      url: 'http://192.168.6.155:8000/strike',
    },
    {
      id: 6,
      url: 'http://192.168.6.156:8000/strike',
    },
    {
      id: 7,
      url: 'http://192.168.6.157:8000/strike',
    },
    {
      id: 8,
      url: 'http://192.168.6.158:8000/strike',
    },
    {
      id: 9,
      url: 'http://192.168.6.159:8000/strike',
    },
    {
      id: 10,
      url: 'http://192.168.6.160:8000/strike',
    },
  ],
  camera_url: [
    {
      id: 1,
      url: '192.168.6.155',
      connection: false,
    },
    // {
    //   id: 2,
    //   url: '192.168.6.153',
    //   connection: false,
    // },
    // {
    //   id: 3,
    //   url: '192.168.6.153',
    //   connection: false,
    // },
    // {
    //   id: 4,
    //   url: '192.168.6.154',
    //   connection: false,
    // },
    // {
    //   id: 5,
    //   url: '192.168.6.155',
    //   connection: false,
    // },
    // {
    //   id: 6,
    //   url: '192.168.6.156',
    //   connection: false,
    // },
    // {
    //   id: 7,
    //   url: '192.168.6.157',
    //   connection: false,
    // },
    // {
    //   id: 8,
    //   url: '192.168.6.158',
    //   connection: false,
    // },
    // {
    //   id: 9,
    //   url: '192.168.6.159',
    //   connection: false,
    // },
    // {
    //   id: 10,
    //   url: '192.168.6.160',
    //   connection: false,
    // },
  ],
};

export default defaults;
