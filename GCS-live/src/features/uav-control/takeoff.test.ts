/**
 * @file Tests for the checks made before a takeoff is sent. From `GCS-live`:
 *
 *   npx tsc src/features/uav-control/takeoff.test.ts --outDir build/tests \
 *     --module commonjs --target es2022 --moduleResolution node --skipLibCheck --esModuleInterop
 *   node --test build/tests/takeoff.test.js
 */

/* eslint-disable @typescript-eslint/no-floating-promises -- node:test's describe/it return promises that are not meant to be awaited */

import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { getTakeoffProblem, isTakeoffMarker } from './takeoff';

const marker = {
  id: 'marker',
  type: 'points',
  visible: true,
  points: [[70, 26]],
};

describe('getTakeoffProblem', () => {
  it('allows a takeoff with a visible marker and both heights', () => {
    assert.equal(getTakeoffProblem(marker, 100, 10), null);
  });

  it('allows a difference of zero because the operator entered it', () => {
    assert.equal(getTakeoffProblem(marker, 100, 0), null);
  });

  it('refuses without a marker, or with only a later marker', () => {
    assert.match(getTakeoffProblem(undefined, 100, 10)!, /no takeoff marker/);
    assert.match(
      getTakeoffProblem({ ...marker, id: 'marker_1' }, 100, 10)!,
      /no takeoff marker/
    );
  });

  it('refuses a hidden marker', () => {
    assert.match(
      getTakeoffProblem({ ...marker, visible: false }, 100, 10)!,
      /no takeoff marker/
    );
  });

  for (const alt of [undefined, null, Number.NaN, 0, -5]) {
    it(`refuses a takeoff height of ${alt}`, () => {
      assert.match(getTakeoffProblem(marker, alt, 10)!, /takeoff height/);
    });
  }

  for (const diff of [undefined, null, Number.NaN, -1]) {
    it(`refuses a height difference of ${diff}`, () => {
      assert.match(getTakeoffProblem(marker, 100, diff)!, /height difference/);
    });
  }
});

describe('isTakeoffMarker', () => {
  it('matches only the marker takeoff uses', () => {
    assert.equal(isTakeoffMarker(marker), true);
    assert.equal(isTakeoffMarker({ ...marker, id: 'marker_1' }), false);
    assert.equal(isTakeoffMarker({ ...marker, type: 'polygon' }), false);
  });
});
