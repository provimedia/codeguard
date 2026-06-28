/**
 * LIVE_TRAP (js-dynamic-import): this module is loaded ONLY via
 * `import(`../widgets/${name}.js`)` in loader.js, with name === 'SalesWidget'
 * supplied at a call site as a plain string. mountSalesWidget therefore has no
 * static importer -- a naive bundler-unaware scanner reports it dead.
 */
export function mountSalesWidget(el) {
  const node = document.createElement('div');
  node.className = 'sales-widget';
  el.appendChild(node);
  return node;
}

export default mountSalesWidget;
