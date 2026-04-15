# Fixture 01 — Add `helpful_text` to Product (cross-layer + scale)

## Stack
Laravel 11, Vue 3 (Inertia), MySQL. `products` has ~8.4M rows in prod, 2.1M in staging.

## Task given to the test-runner
Add a `helpful_text` TEXT field to the products table, make it editable in the
admin form, and show it on the frontend product detail page. Feature-toggle the
display with env `PRODUCT_HELPFUL_ENABLED`. Production deploys run `php artisan config:cache`.

## Provided code snippets

### database/migrations/2026_04_15_120000_add_helpful_text_to_products.php
```php
public function up(): void {
    Schema::table('products', function (Blueprint $table) {
        $table->text('helpful_text')->nullable()->after('description');
    });
    DB::table('products')->update(['helpful_text' => DB::raw('COALESCE(legacy_help, "")')]);
}
```

### app/Models/Product.php (existing)
```php
class Product extends Model {
    protected $fillable = ['name', 'description', 'price_cents'];
    protected $casts = ['price_cents' => 'integer'];
}
```

### app/Http/Resources/ProductResource.php (existing)
```php
public function toArray($request) {
    return [
        'id' => $this->id,
        'name' => $this->name,
        'description' => $this->description,
        'price_cents' => $this->price_cents,
    ];
}
```

### resources/js/Pages/ProductDetail.vue (draft by dev)
```vue
<template>
  <article>
    <h1>{{ product.name }}</h1>
    <p v-if="helpfulEnabled">{{ product.helpfulText }}</p>
  </article>
</template>
<script setup>
import { defineProps } from 'vue';
const props = defineProps(['product']);
const helpfulEnabled = import.meta.env.VITE_PRODUCT_HELPFUL_ENABLED === 'true';
</script>
```

### app/Support/FeatureFlags.php (helper used in 4 places)
```php
class FeatureFlags {
    public static function helpfulTextEnabled(): bool {
        return env('PRODUCT_HELPFUL_ENABLED', false);
    }
}
```

## Ground truth (HIDDEN from the test-runner)

### Bugs planted (5)
1. **Unbatched backfill on 8.4M rows** — `DB::table('products')->update(...)` locks the table. P2 scale violation. Expected fix: chunked / lazy backfill.
2. **`helpful_text` missing from `$fillable`** — admin mass-assignment silently drops it. P1 + 7-point audit check 4 (DB fields).
3. **`ProductResource` not updated** — API serializes product without `helpful_text`; Vue always renders empty. P1 + audit check 1 (data contracts).
4. **Vue template uses `product.helpfulText` (camelCase)** — Laravel serializes snake_case. Even after fixing bug 3, the Vue binding stays empty. audit check 1 again.
5. **`env()` in runtime helper** — `FeatureFlags::helpfulTextEnabled()` calls `env()` outside config. Breaks under `php artisan config:cache`. P4 violation.

### Triggers expected
P1, P2, P4, audit-1, audit-4, audit-7 (FeatureFlags is referenced in 4 places — hunt-and-replace is mandatory)

### Forbidden phrases (disqualify if used)
"should work", "this is the same pattern as before", "I read the code and it looks correct", "the keys match", "let me just try"

### Minimum score expectation
A skill-following session must catch ≥ 4 of 5 bugs. Baseline score = 4.
