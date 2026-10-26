import React, { useCallback, useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@material-ui/core';

import messageHub from '~/message-hub';
import { showError } from '~/features/snackbar/actions';
import { showNotification } from '~/features/snackbar/slice';
import { MessageSemantics } from '~/features/snackbar/types';

const POLL_MS = 3000;

const REASONS = {
  not_registered: 'This UAV has no registered onboard computer',
  unreachable: 'Its onboard computer does not answer',
  already_master: 'It is already the master',
  promotion_in_progress: 'A promotion is already in progress on it',
  node_epoch_ahead: 'It is ahead of the server (stale server state)',
  node_not_in_decentralised_mode: 'Its swarm program has no SWARM_NODE_ID set',
  legacy_mode_single_computer:
    'No node table configured (single-computer mode)',
};

const send = (message, extra = {}) =>
  messageHub.sendMessage({
    type: 'X-UAV-socket',
    message,
    ids: [],
    ...extra,
  });

/**
 * Master selection + live node status. Everything shown here (role,
 * reachability, queue depth) is reported by the onboard computers
 * themselves, not inferred from what was last sent to them.
 */
const MasterSelector = () => {
  const dispatch = useDispatch();
  const [status, setStatus] = useState(null);
  const [pending, setPending] = useState(null); // { node, check }
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await send('swarm_status');
      if (res?.body?.message && typeof res.body.message === 'object') {
        setStatus(res.body.message);
      }
    } catch (e) {
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  const askToPromote = async (node) => {
    try {
      const res = await send('master', { ids: [node], confirm: false });
      setPending({ node, check: res?.body?.message });
    } catch (e) {
      dispatch(showError(`Master check failed: ${e?.message}`));
    }
  };

  const confirmPromote = async () => {
    const { node } = pending;
    setBusy(true);
    try {
      const res = await send('master', { ids: [node], confirm: true });
      const out = res?.body?.message;
      if (out?.ok) {
        dispatch(
          showNotification({
            message: `UAV ${node} is promoting to master (epoch ${out.epoch})${
              out.old_master_demoted === false
                ? ' — old master not reachable, it will be demoted when it returns'
                : ''
            }`,
            semantics: MessageSemantics.SUCCESS,
          })
        );
      } else {
        dispatch(showError(`Master change refused: ${out?.reason}`));
      }
    } catch (e) {
      dispatch(showError(`Master change failed: ${e?.message}`));
    } finally {
      setBusy(false);
      setPending(null);
      refresh();
    }
  };

  if (!status) {
    return null;
  }
  if (status.load_error) {
    return (
      <Typography color='error'>Swarm node table: {status.load_error}</Typography>
    );
  }
  if (status.legacy) {
    return (
      <Typography variant='caption'>
        Swarm: single-computer mode (no node table)
      </Typography>
    );
  }

  const masterNode = status.nodes.find((n) => n.id === status.master);
  const recovery = masterNode?.status?.recovery;

  const resumeRecovery = async () => {
    if (
      !window.confirm(
        `Resume ${recovery.resumable} goal task(s) from the failed master's last state? ` +
          'Only tasks re-verified against live UAV telemetry are resumed; search/split work and ' +
          `${recovery.unknown_commands} command(s) with unknown outcome must be re-issued by you.`
      )
    ) {
      return;
    }
    try {
      const res = await send('recover_resume');
      const out = res?.body?.message;
      dispatch(
        out?.ok
          ? showNotification({
              message: `Recovery resume sent (replica v${out.version})`,
              semantics: MessageSemantics.SUCCESS,
            })
          : showError(`Recovery not sent: ${out?.reason || 'unknown'}`)
      );
    } catch (e) {
      dispatch(showError(`Recovery failed: ${e?.message}`));
    }
  };

  const check = pending?.check;
  const reasons = (check?.reasons || []).map((r) => REASONS[r] || r);

  return (
    <Box style={{ margin: '4px 0 12px' }}>
      <Typography variant='subtitle2'>
        Swarm master:{' '}
        {status.master == null ? 'NONE SELECTED — commands are refused' : `UAV ${status.master}`}{' '}
        (epoch {status.epoch})
        {status.pending_demotions?.length
          ? ` — waiting to demote UAV ${status.pending_demotions.join(', ')}`
          : ''}
      </Typography>
      {status.master_health?.lost && (
        <Typography color='error' style={{ fontWeight: 600 }}>
          Master UAV {status.master} is NOT responding ({status.master_health.missed}{' '}
          missed heartbeats). Nothing was promoted automatically — pick a new
          master below if it has really failed.
        </Typography>
      )}
      {recovery && (
        <Typography variant='body2' style={{ marginTop: 4 }}>
          Recovered replica v{recovery.version}: {recovery.resumable} goal
          task(s) verified,
          {' '}{recovery.needs_operator} need you to re-issue,
          {' '}{recovery.unknown_commands} command(s) with unknown outcome.{' '}
          {recovery.resumable > 0 && (
            <Button size='small' variant='outlined' onClick={resumeRecovery}>
              Resume verified goals
            </Button>
          )}
        </Typography>
      )}
      <Box style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
        {status.nodes.map((n) => {
          const st = n.status || {};
          const role = !n.reachable
            ? 'OFFLINE'
            : st.promoting
            ? 'promoting…'
            : st.role;
          return (
            <Button
              key={n.id}
              size='small'
              variant={n.id === status.master ? 'contained' : 'outlined'}
              color={n.reachable ? 'primary' : 'default'}
              disabled={busy}
              onClick={() => askToPromote(n.id)}
              title={`${n.ip}${st.queued ? ` · ${st.queued} queued` : ''}`}
            >
              UAV {n.id} · {role}
            </Button>
          );
        })}
      </Box>
      {status.commands?.length > 0 && (
        <Typography variant='caption' component='div' style={{ marginTop: 6 }}>
          Last commands:{' '}
          {status.commands
            .slice(-4)
            .map((c) => `${c.cmd.split(/[_,]/)[0]}→UAV${c.node}: ${c.status}${c.why ? ` (${c.why})` : ''}`)
            .join('  |  ')}
        </Typography>
      )}

      <Dialog open={Boolean(pending)} onClose={() => setPending(null)}>
        <DialogTitle>Make UAV {pending?.node} the swarm master?</DialogTitle>
        <DialogContent>
          {check?.eligible ? (
            <Typography>
              The current master (UAV {status.master ?? '—'}) will be told to
              stand down and UAV {pending?.node} will take over command of the
              whole swarm. Only do this when the current master has failed or you
              mean to hand over.
            </Typography>
          ) : (
            <>
              <Typography color='error'>Not eligible:</Typography>
              {reasons.map((r) => (
                <Typography key={r}>• {r}</Typography>
              ))}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPending(null)}>Cancel</Button>
          <Button
            color='primary'
            variant='contained'
            disabled={!check?.eligible || busy}
            onClick={confirmPromote}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MasterSelector;
