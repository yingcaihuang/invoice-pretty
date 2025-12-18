import { useEffect, useRef, useCallback } from 'react';

interface PollingOptions {
  interval: number;
  enabled: boolean;
  maxRetries?: number;
  backoffMultiplier?: number;
}

export const usePolling = (
  callback: () => Promise<void>,
  options: PollingOptions
) => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const currentIntervalRef = useRef(options.interval);

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (!options.enabled) {
      return;
    }

    const poll = async () => {
      try {
        await callback();
        // Reset retry count and interval on success
        retryCountRef.current = 0;
        currentIntervalRef.current = options.interval;
      } catch (error) {
        console.error('Polling error:', error);
        
        // Implement exponential backoff
        if (options.maxRetries && retryCountRef.current < options.maxRetries) {
          retryCountRef.current++;
          currentIntervalRef.current *= options.backoffMultiplier || 2;
        }
      }
    };

    // Initial poll
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, currentIntervalRef.current);
  }, [callback, options.enabled, options.interval, options.maxRetries, options.backoffMultiplier]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    retryCountRef.current = 0;
    currentIntervalRef.current = options.interval;
  }, [options.interval]);

  useEffect(() => {
    if (options.enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    return stopPolling;
  }, [options.enabled, startPolling, stopPolling]);

  return { startPolling, stopPolling };
};