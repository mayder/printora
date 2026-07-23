type TimerHandle = ReturnType<typeof globalThis.setTimeout>;
type Schedule = (callback: () => void, delayMs: number) => TimerHandle;
type Cancel = (handle: TimerHandle) => void;

export function startSequentialPoll(
  task: () => Promise<void>,
  delayMs: number,
  schedule: Schedule = globalThis.setTimeout,
  cancel: Cancel = globalThis.clearTimeout,
): () => void {
  let stopped = false;
  let timer: TimerHandle | undefined;

  const run = async () => {
    try {
      await task();
    } finally {
      if (!stopped) {
        timer = schedule(() => void run(), delayMs);
      }
    }
  };

  void run();
  return () => {
    stopped = true;
    if (timer !== undefined) {
      cancel(timer);
    }
  };
}
