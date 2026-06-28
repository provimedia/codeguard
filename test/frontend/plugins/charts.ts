interface AxisOptions {
  min: number;
  max: number;
}

// Real exported helper (the public surface of this plugin).
export function buildAxisTicks(opts: AxisOptions): number[] {
  const ticks: number[] = [];
  for (let v = opts.min; v <= opts.max; v += (opts.max - opts.min) / 4) {
    ticks.push(Math.round(v));
  }
  return ticks;
}

/**
 * DEAD (ts-private-class): a module-local (non-exported) class that nothing
 * instantiates or references. Equivalent of a "private" class. Removable.
 */
class LegacyAxisFormatter {
  format(value: number): string {
    return value.toFixed(0);
  }
}
