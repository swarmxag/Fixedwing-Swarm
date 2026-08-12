/**
 * @file File that re-exports all the individual views implemented in
 * other files in this folder.
 */

import BeaconList from './beacons';
import ClockDisplayList from './clocks';
import ConnectionList from './connections';
import DatasetList from './datasets';
import DockList from './docks';
import FeatureList from './features';
import LayerList from './layers';
import LCDClockPanel from './lcd-clock';
import LightControlPanel from './light-control';
import SavedLocationList from './locations';
import LogPanel from './log';
import MessagesPanelView from './messages';
import ShowControlPanel from './show-control';
import UAVList from './uavs';
import ThreeDTopLevelView from './three-d';
import StrikePanel from './stike';
import CameraPanel from './camera';
import SwarmPanel from './swarm';
import SpareDronePanel from './spareDrone';
import VtolPanel from './VTOL';
import TargetCNF from './gimbalTarget';
import AltitudeSettings from './altitudeSettings';
import SimulatorPanel from './simulator';
/* MapView not included as it is loaded lazily */

const views = {
  BeaconList,
  ClockDisplayList,
  ConnectionList,
  DatasetList,
  DockList,
  FeatureList,
  LayerList,
  LCDClockPanel,
  LightControlPanel,
  LogPanel,
  MessagesPanelView,
  SavedLocationList,
  ShowControlPanel,
  UAVList,
  ThreeDTopLevelView,
  StrikePanel,
  CameraPanel,
  SwarmPanel,
  SpareDronePanel,
  VtolPanel,
  TargetCNF,
  AltitudeSettings,
  SimulatorPanel
};

export default views;
