import { Status } from '@skybrush/app-theme-material-ui';

/**
 * Pseudo-status of a UAV that was excluded (removed) from the swarm. It is not
 * part of the shared `Status` enum because the theme package has no colour for
 * it; the components that draw UAV statuses give it a purple colour themselves.
 */
export const EXCLUDED_STATUS = 'excluded';

const prioritiesForStatuses: Record<string, number> = {
  [Status.CRITICAL]: 100,
  [Status.ERROR]: 90,
  [Status.WARNING]: 80,
  [Status.MISSING]: 70,
  [Status.RTH]: 60,
  [EXCLUDED_STATUS]: 55,
  [Status.SKIPPED]: 50,
  [Status.NEXT]: 40,
  [Status.INFO]: 30,
  [Status.SUCCESS]: 20,
  [Status.WAITING]: 10,
  [Status.OFF]: 0,
};

export const statusToPriority = (status: Status | typeof EXCLUDED_STATUS): number =>
  prioritiesForStatuses[status] ?? 0;

export { Status } from '@skybrush/app-theme-material-ui';
