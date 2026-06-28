import { createApp } from 'vue';
import App from './App.vue';
import { loadWidget } from './utils/loader.js';

/*
 * Components are auto-registered from a glob. Note there is NO explicit
 * `import UserCard from ...` -- UserCard.vue and SalesChart.vue are referenced
 * ONLY by their template tag name / by a dynamic :is string. A naive scanner
 * that looks for `import <Component>` finds nothing and flags them dead.
 */
const app = createApp(App);

const modules = import.meta.glob('./components/*.vue', { eager: true });
for (const [path, mod] of Object.entries(modules)) {
  const name = path.split('/').pop().replace('.vue', '');
  app.component(name, mod.default);
}

// Lazy widget: the file name is a runtime string; the widget's exported symbol
// is never statically imported.
loadWidget('SalesWidget').then((mount) => mount && mount(document.body));

app.mount('#app');
