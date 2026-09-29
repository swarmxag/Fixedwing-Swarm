import { type LabelStyle } from '~/model/features';
import { type Identifier } from '~/utils/collections';

export enum FeatureEditorTab {
  GENERAL = 'general',
  POINTS = 'points',
}

export type FeatureProperties = {
  color?: string;
  filled: boolean;
  id: Identifier;
  label?: string;
  labelStyle?: LabelStyle;
  measure: boolean;
  showPoints: boolean;
  visible: boolean;
  // Whether the "Automate Goals" plan overlay (one loiter circle per UAV,
  // the spine and the safety-margin gap) is drawn for this feature. Opt-in
  // per feature via the map context menu, so anchoring a point no longer
  // draws the whole layout unasked.
  showPlan?: boolean;
};
