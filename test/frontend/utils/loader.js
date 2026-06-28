import { debounce } from './timing.js'; // DEAD (js-unused-import): debounce is never used here.

/**
 * Loads a widget module by name. The path is COMPUTED, so the target module's
 * exported symbol (mountSalesWidget) is reachable only at runtime -- no static
 * importer exists for it. (LIVE_TRAP support: js-dynamic-import.)
 */
export async function loadWidget(name) {
  const mod = await import(`../widgets/${name}.js`);
  return mod.default ?? null;
}
