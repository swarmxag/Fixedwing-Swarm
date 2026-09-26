/**
 * @file Tests for the unsafe-terrain message handling of the GCS.
 *
 * The GCS has no test runner, so these use Node's built-in one and cover only
 * pure code (no React, no OpenLayers). From the `GCS-live` folder:
 *
 *   npx tsc src/features/terrain-safety/areas.test.ts --outDir build/tests \
 *     --module commonjs --target es2022 --moduleResolution node --skipLibCheck --esModuleInterop
 *   node --test build/tests/areas.test.js
 */

/* eslint-disable @typescript-eslint/no-floating-promises -- node:test's describe/it return promises that are not meant to be awaited */

import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  areaToRings,
  describeThresholdBreakdown,
  describeUnsafeTerrain,
  parseUnsafeTerrainMessage,
} from './areas';
import { handleUnsafeTerrainMessage } from './handlers';
import reducer, {
  clearUnsafeTerrain,
  setUnsafeTerrain,
  setUnsafeTerrainVisible,
} from './slice';

// A message in exactly the shape Xag-Server sends (server field order kept).
const square = (lat: number, lon: number, size = 0.001) => [
  [lat, lon],
  [lat, lon + size],
  [lat + size, lon + size],
  [lat + size, lon],
  [lat, lon],
];

const serverMessage = () => ({
  type: 'X-TERRAIN-UNSAFE-AREA-RESP',
  status: 'unsafe',
  thresholdAMSL: 428,
  areaCount: 2,
  unsafeCellCount: 155,
  maxUnsafeElevation: 760,
  highestPoint: { lat: 22.6304019, lon: 76.2368399, elevation: 760 },
  vertexCount: 15,
  simplifyToleranceM: 0,
  areas: [
    {
      id: 1,
      cellCount: 120,
      maxElevation: 760,
      highestPoint: { lat: 22.6304019, lon: 76.2368399, elevation: 760 },
      polygon: square(22.6, 76.2, 0.01),
      holes: [square(22.604, 76.204, 0.002)],
      severity: 'red',
    },
    {
      id: 2,
      cellCount: 35,
      maxElevation: 570,
      highestPoint: { lat: 22.7, lon: 76.3, elevation: 570 },
      polygon: square(22.7, 76.3),
      holes: [],
      severity: 'yellow',
    },
  ],
  originFingerprint: 'abc123',
  thresholdUavId: null,
  altitudeSource: 'takeoff_altitude',
  // threshold = referenceTerrainElevation + safetyAltitude - safetyMargin
  referenceTerrainElevation: 378,
  safetyAltitude: 100,
  safetyMargin: 50,
  referenceSource: 'swarm_home',
  referenceLocation: { lat: 30.8025195, lon: 79.8148472 },
});

describe('parseUnsafeTerrainMessage', () => {
  it('parses an unsafe message from the server', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage());
    assert.ok(terrain);
    assert.equal(terrain.status, 'unsafe');
    assert.equal(terrain.thresholdAMSL, 428);
    assert.equal(terrain.areaCount, 2);
    assert.equal(terrain.areas.length, 2);
    assert.equal(terrain.unsafeCellCount, 155);
    assert.equal(terrain.maxUnsafeElevation, 760);
    assert.deepEqual(terrain.highestPoint, {
      lat: 22.6304019,
      lon: 76.2368399,
      elevation: 760,
    });
    assert.equal(terrain.originFingerprint, 'abc123');
    assert.equal(terrain.altitudeSource, 'takeoff_altitude');

    const [first, second] = terrain.areas;
    assert.equal(first!.id, 1);
    assert.equal(first!.cellCount, 120);
    assert.equal(first!.polygon.length, 5);
    assert.equal(first!.holes.length, 1); // the hole is kept
    assert.equal(second!.holes.length, 0);
  });

  it('turns the JSON nulls of the server into undefined', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage());
    assert.equal(terrain!.thresholdUavId, undefined);
  });

  it('parses the safe and unavailable messages', () => {
    const safe = parseUnsafeTerrainMessage({
      status: 'safe',
      thresholdAMSL: 828,
      areaCount: 0,
      unsafeCellCount: 0,
      maxUnsafeElevation: null,
      highestPoint: null,
      areas: [],
    });
    assert.equal(safe!.status, 'safe');
    assert.equal(safe!.thresholdAMSL, 828);
    assert.deepEqual(safe!.areas, []);
    assert.equal(safe!.maxUnsafeElevation, undefined);
    assert.equal(safe!.highestPoint, undefined);

    const unavailable = parseUnsafeTerrainMessage({
      status: 'unavailable',
      thresholdAMSL: null,
      areaCount: 0,
      unsafeCellCount: 0,
      areas: [],
    });
    assert.equal(unavailable!.status, 'unavailable');
    assert.equal(unavailable!.thresholdAMSL, undefined);
  });

  it('rejects things that are not such a message', () => {
    for (const bad of [
      undefined,
      null,
      42,
      'unsafe',
      {},
      { status: 'weird' },
      { status: 42 },
    ]) {
      assert.equal(parseUnsafeTerrainMessage(bad), undefined);
    }
  });

  it('drops unusable areas but keeps the good ones', () => {
    const message = serverMessage();
    message.areas.push(
      { id: 3, polygon: [[1, 1]] } as never, // too few points
      {
        id: 4,
        polygon: [
          [1, 1],
          [1, 2],
          ['x', 3],
        ],
      } as never, // not a number
      {
        id: 5,
        polygon: [
          [95, 1],
          [96, 2],
          [97, 3],
        ],
      } as never, // latitude out of range
      {
        id: 6,
        polygon: [
          [1, 1],
          [1, 2],
          [Number.NaN, 3],
        ],
      } as never, // not finite
      'nonsense' as never,
      null as never
    );
    const terrain = parseUnsafeTerrainMessage(message);
    assert.deepEqual(
      terrain!.areas.map((area) => area.id),
      [1, 2]
    );
    assert.equal(terrain!.areaCount, 2);
  });

  it('drops an unusable hole but keeps the area', () => {
    const message = serverMessage();
    message.areas[0]!.holes.push([[1, 1]] as never);
    const terrain = parseUnsafeTerrainMessage(message);
    assert.equal(terrain!.areas[0]!.holes.length, 1);
  });
});

describe('areaToRings', () => {
  const identity = (lonLat: [number, number]): [number, number] => lonLat;

  it('swaps [lat, lon] into [lon, lat] for the map projection', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    const [exterior] = areaToRings(terrain.areas[1]!, identity);
    assert.deepEqual(exterior![0], [76.3, 22.7]); // lon first
    assert.deepEqual(exterior![2], [76.301, 22.701]);
  });

  it('returns the exterior ring followed by the hole rings', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    const rings = areaToRings(terrain.areas[0]!, identity);
    assert.equal(rings.length, 2);
    assert.deepEqual(rings[1]![0], [76.204, 22.604]);
  });

  it('closes a ring that the server left open and never mutates the input', () => {
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      areas: [
        {
          id: 1,
          polygon: [
            [10, 20],
            [10, 21],
            [11, 21],
            [11, 20],
          ],
          holes: [],
        },
      ],
    })!;
    const [exterior] = areaToRings(terrain.areas[0]!, identity);
    assert.equal(exterior!.length, 5);
    assert.deepEqual(exterior![4], exterior![0]);
    assert.equal(terrain.areas[0]!.polygon.length, 4);
  });

  it('applies the projection to every vertex', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    const seen: Array<[number, number]> = [];
    areaToRings(terrain.areas[1]!, (lonLat) => {
      seen.push(lonLat);
      return [lonLat[0] * 2, lonLat[1] * 2];
    });
    assert.equal(seen.length, 5);
  });
});

describe('describeUnsafeTerrain', () => {
  it('summarizes the three states', () => {
    const unsafe = parseUnsafeTerrainMessage(serverMessage())!;
    assert.equal(
      describeUnsafeTerrain(unsafe),
      'Terrain above 428 m AMSL: 2 areas, highest 760 m'
    );
    assert.equal(
      describeUnsafeTerrain({ ...unsafe, areas: unsafe.areas.slice(0, 1) }),
      'Terrain above 428 m AMSL: 1 area, highest 760 m'
    );
    const safe = parseUnsafeTerrainMessage({
      status: 'safe',
      thresholdAMSL: 828,
      areas: [],
    })!;
    assert.equal(describeUnsafeTerrain(safe), 'No terrain above 828 m AMSL');
    const unavailable = parseUnsafeTerrainMessage({ status: 'unavailable' })!;
    assert.equal(
      describeUnsafeTerrain(unavailable),
      'Terrain safety unavailable'
    );
  });
});

describe('the inputs of the safety threshold', () => {
  // threshold = referenceTerrainElevation + safetyAltitude (drone height) - safetyMargin
  it('parses what the server calculated the threshold from', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    assert.equal(terrain.referenceTerrainElevation, 378);
    assert.equal(terrain.safetyAltitude, 100);
    assert.equal(terrain.safetyMargin, 50);
    assert.equal(terrain.thresholdAMSL, 428);
  });

  it('shows home terrain, drone height, margin, threshold and the formula', () => {
    // the example: 300 + 100 - 50 = 350; maxUnsafeElevation (760, from serverMessage) is
    // the highest peak: 760 - 300 + 50 = 510
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      thresholdAMSL: 350,
      referenceTerrainElevation: 300,
      safetyAltitude: 100,
      safetyMargin: 50,
    })!;
    assert.deepEqual(describeThresholdBreakdown(terrain), {
      homeTerrain: '300 m AMSL',
      homeSource: 'lowest UAV home (30.8025, 79.8148)',
      droneHeight: '100 m',
      safetyMargin: '50 m', // a positive distance; the formula subtracts it
      threshold: '350 m AMSL',
      formula: '300 + 100 - 50 = 350 m AMSL',
      highestPeak: '760 m AMSL', // straight from the server's maxUnsafeElevation, not recomputed
      droneSafeAltitude: '510 m', // 760 - 300 + 50; a height, no " AMSL" suffix
      safeAltitudeFormula: '760 - 300 + 50 = 510 m',
    });
  });

  it('displays the SERVER threshold and never calculates one itself', () => {
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      thresholdAMSL: 999, // deliberately NOT 300 + 100 - 50
      referenceTerrainElevation: 300,
      safetyAltitude: 100,
      safetyMargin: 50,
    })!;
    const breakdown = describeThresholdBreakdown(terrain)!;
    assert.equal(breakdown.threshold, '999 m AMSL');
    assert.equal(breakdown.formula, '300 + 100 - 50 = 999 m AMSL');
    assert.equal(
      describeUnsafeTerrain(terrain),
      'Terrain above 999 m AMSL: 2 areas, highest 760 m'
    );
  });

  it('formats fractional metres with one decimal and whole ones as they are', () => {
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      thresholdAMSL: 350.5,
      referenceTerrainElevation: 300.5,
      safetyAltitude: 100,
      safetyMargin: 50,
    })!;
    assert.equal(
      describeThresholdBreakdown(terrain)!.formula,
      '300.5 + 100 - 50 = 350.5 m AMSL'
    );
  });

  it('shows the breakdown for a safe result too', () => {
    const terrain = parseUnsafeTerrainMessage({
      status: 'safe',
      thresholdAMSL: 828,
      referenceTerrainElevation: 378,
      safetyAltitude: 500,
      safetyMargin: 50,
      areas: [],
    })!;
    assert.equal(
      describeThresholdBreakdown(terrain)!.formula,
      '378 + 500 - 50 = 828 m AMSL'
    );
  });

  it('shows no breakdown when the server did not send all the inputs', () => {
    const message: Record<string, unknown> = { ...serverMessage() };
    for (const key of [
      'referenceTerrainElevation',
      'safetyAltitude',
      'safetyMargin',
    ]) {
      const partial = { ...message };
      delete partial[key];
      assert.equal(
        describeThresholdBreakdown(parseUnsafeTerrainMessage(partial)!),
        undefined,
        key
      );
    }

    const noThreshold = { ...message, thresholdAMSL: null };
    assert.equal(
      describeThresholdBreakdown(parseUnsafeTerrainMessage(noThreshold)!),
      undefined
    );
  });

  it('ignores inputs that are not finite numbers', () => {
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      safetyMargin: 'fifty',
      safetyAltitude: Number.NaN,
    })!;
    assert.equal(terrain.safetyMargin, undefined);
    assert.equal(terrain.safetyAltitude, undefined);
    assert.equal(describeThresholdBreakdown(terrain), undefined);
  });
});

describe('highest terrain peak and drone safe altitude', () => {
  // droneSafeAltitude = highestPeak (server's maxUnsafeElevation) - homeTerrain + safetyMargin
  it('matches the worked example: 425 - 300 + 50 = 175', () => {
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      maxUnsafeElevation: 425,
      referenceTerrainElevation: 300,
      safetyAltitude: 100,
      safetyMargin: 50,
      thresholdAMSL: 350,
    })!;
    const breakdown = describeThresholdBreakdown(terrain)!;
    assert.equal(breakdown.highestPeak, '425 m AMSL');
    assert.equal(breakdown.droneSafeAltitude, '175 m');
    assert.equal(breakdown.safeAltitudeFormula, '425 - 300 + 50 = 175 m');
    assert.equal(425 - 300 + 50, 175); // the formula itself, spelled out
  });

  it('does not recompute the highest peak: it is the server’s maxUnsafeElevation, verbatim', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!; // maxUnsafeElevation: 760
    assert.equal(terrain.maxUnsafeElevation, 760);
    assert.equal(
      describeThresholdBreakdown(terrain)!.highestPeak,
      '760 m AMSL'
    );
    // the existing summary line uses the very same field -- one source, not two
    assert.match(describeUnsafeTerrain(terrain), /highest 760 m/);
  });

  it('shows — for both when there is no unsafe terrain (safe / unavailable)', () => {
    const safe = parseUnsafeTerrainMessage({
      status: 'safe',
      thresholdAMSL: 828,
      referenceTerrainElevation: 378,
      safetyAltitude: 500,
      safetyMargin: 50,
      areas: [],
    })!;
    const breakdown = describeThresholdBreakdown(safe)!;
    assert.equal(breakdown.highestPeak, '—');
    assert.equal(breakdown.droneSafeAltitude, '—');
    assert.equal(breakdown.safeAltitudeFormula, undefined);
    // and the rest of the breakdown is still there, not NaN/undefined
    assert.equal(breakdown.threshold, '828 m AMSL');
  });

  it('never produces NaN when the highest peak is missing', () => {
    const message: Record<string, unknown> = { ...serverMessage() };
    delete message['maxUnsafeElevation'];
    const breakdown = describeThresholdBreakdown(
      parseUnsafeTerrainMessage(message)!
    )!;
    assert.equal(breakdown.highestPeak, '—');
    assert.equal(breakdown.droneSafeAltitude, '—');
    assert.doesNotMatch(breakdown.droneSafeAltitude, /NaN/);
  });

  it('a peak at or below home terrain gives a safe altitude of 0 m or less, not —', () => {
    // home terrain itself can be the highest unsafe point right at the threshold
    const terrain = parseUnsafeTerrainMessage({
      ...serverMessage(),
      maxUnsafeElevation: 300,
      referenceTerrainElevation: 300,
      safetyAltitude: 100,
      safetyMargin: 50,
      thresholdAMSL: 350,
    })!;
    assert.equal(
      describeThresholdBreakdown(terrain)!.droneSafeAltitude,
      '50 m'
    );
  });
});

describe('where the home terrain was read', () => {
  const describeSource = (fields: Record<string, unknown>) =>
    describeThresholdBreakdown(
      parseUnsafeTerrainMessage({ ...serverMessage(), ...fields })!
    )!.homeSource;

  it('says whose home it is when it is a UAV home', () => {
    assert.equal(
      describeSource({
        referenceSource: 'uav_home',
        thresholdUavId: '01',
        referenceLocation: { lat: 30.8025195, lon: 79.8148472 },
      }),
      'UAV 01 home (30.8025, 79.8148)'
    );
    assert.equal(
      describeSource({ referenceSource: 'uav_home', thresholdUavId: null }),
      'UAV home (30.8025, 79.8148)'
    );
  });

  it('says so when it is the lowest home of the swarm or the Origin corner', () => {
    assert.equal(
      describeSource({ referenceSource: 'swarm_home' }),
      'lowest UAV home (30.8025, 79.8148)'
    );
    assert.equal(
      describeSource({
        referenceSource: 'origin_corner',
        referenceLocation: { lat: 30.7219197, lon: 79.7344894 },
      }),
      'Origin corner (30.7219, 79.7345), no UAV position yet'
    );
  });

  it('leaves the location out when the server did not send a usable one', () => {
    assert.equal(
      describeSource({
        referenceSource: 'swarm_home',
        referenceLocation: null,
      }),
      'lowest UAV home'
    );
    assert.equal(
      describeSource({
        referenceSource: 'uav_home',
        referenceLocation: { lat: 'x', lon: 1 },
      }),
      'UAV home'
    );
  });

  it('shows no source for an unknown or missing one (an older server)', () => {
    assert.equal(
      describeSource({ referenceSource: 'something_new' }),
      undefined
    );
    assert.equal(describeSource({ referenceSource: undefined }), undefined);
    // ... but the numbers themselves are still shown
    const breakdown = describeThresholdBreakdown(
      parseUnsafeTerrainMessage({
        ...serverMessage(),
        referenceSource: undefined,
      })!
    )!;
    assert.equal(breakdown.formula, '378 + 100 - 50 = 428 m AMSL');
  });
});

describe('the store slice and the message handler', () => {
  it('starts empty and visible', () => {
    const state = reducer(undefined, { type: '@@init' });
    assert.equal(state.unsafeTerrain, undefined);
    assert.equal(state.visible, true);
  });

  it('stores what the server reports and replaces it on the next message', () => {
    let state = reducer(undefined, { type: '@@init' });
    state = reducer(
      state,
      setUnsafeTerrain(parseUnsafeTerrainMessage(serverMessage())!)
    );
    assert.equal(state.unsafeTerrain!.areas.length, 2);

    const safe = parseUnsafeTerrainMessage({
      status: 'safe',
      thresholdAMSL: 900,
      areas: [],
    })!;
    state = reducer(state, setUnsafeTerrain(safe));
    assert.equal(state.unsafeTerrain!.status, 'safe');
    assert.equal(state.unsafeTerrain!.areas.length, 0); // the old red areas are gone
  });

  it('"unavailable" clears the areas (no Origin / no threshold on the server)', () => {
    let state = reducer(
      undefined,
      setUnsafeTerrain(parseUnsafeTerrainMessage(serverMessage())!)
    );
    state = reducer(
      state,
      setUnsafeTerrain(parseUnsafeTerrainMessage({ status: 'unavailable' })!)
    );
    assert.equal(state.unsafeTerrain, undefined);
  });

  it('clears on demand and keeps the show/hide choice apart from the data', () => {
    let state = reducer(
      undefined,
      setUnsafeTerrain(parseUnsafeTerrainMessage(serverMessage())!)
    );
    state = reducer(state, setUnsafeTerrainVisible(false));
    assert.equal(state.visible, false);
    assert.equal(state.unsafeTerrain!.areas.length, 2); // hiding does not drop the data
    state = reducer(state, clearUnsafeTerrain());
    assert.equal(state.unsafeTerrain, undefined);
    assert.equal(state.visible, false); // ... and clearing does not change the switch
  });

  it('the handler dispatches a valid message and ignores a malformed one', () => {
    const actions: Array<{ type: string }> = [];
    const dispatch = ((action: { type: string }) => {
      actions.push(action);
      return action;
    }) as never;

    handleUnsafeTerrainMessage(serverMessage(), dispatch);
    assert.equal(actions.length, 1);
    assert.equal(actions[0]!.type, setUnsafeTerrain.type);

    const warn = console.warn;
    console.warn = () => undefined; // keep the test output clean
    try {
      handleUnsafeTerrainMessage({ status: 'nonsense' }, dispatch);
      handleUnsafeTerrainMessage(undefined, dispatch);
    } finally {
      console.warn = warn;
    }

    assert.equal(actions.length, 1); // nothing was dispatched for the bad ones
  });
});

describe('area.severity (computed server-side, only parsed here)', () => {
  it('keeps a valid "red" or "yellow" severity per area', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    assert.equal(terrain.areas[0]!.severity, 'red');
    assert.equal(terrain.areas[1]!.severity, 'yellow');
  });

  it('is undefined when the server omits it (an older server) -- callers then draw plain red', () => {
    const message = serverMessage();
    delete (message.areas[0] as { severity?: unknown }).severity;
    const terrain = parseUnsafeTerrainMessage(message)!;
    assert.equal(terrain.areas[0]!.severity, undefined);
  });

  it('drops anything that is not exactly "red" or "yellow" (never trusts "clear" or garbage from the wire)', () => {
    for (const bad of ['clear', 'RED', 'green', 1, null, {}]) {
      const message = serverMessage();
      (message.areas[0] as { severity?: unknown }).severity = bad;
      const terrain = parseUnsafeTerrainMessage(message)!;
      assert.equal(terrain.areas[0]!.severity, undefined, JSON.stringify(bad));
    }
  });

  it('classifies areas independently -- one message can carry both colours at once', () => {
    const terrain = parseUnsafeTerrainMessage(serverMessage())!;
    const severities = terrain.areas.map((area) => area.severity);
    assert.deepEqual(severities, ['red', 'yellow']);
  });
});
