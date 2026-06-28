<?php

namespace App\Services;

/**
 * Builds report payloads. Several methods here are dispatched purely by string
 * (DB-driven or reflection), which is exactly the pattern a naive dead-code
 * scanner mis-reads as unused.
 */
class ReportBuilder
{
    /**
     * Driver: the *method name* arrives from a database row (see
     * database/seeders/ReportSeeder.php -> reports.method = 'monthlyRevenue').
     * This is real, productive indirection.
     */
    public function run(string $method): array
    {
        // DB-driven dispatch: $method came from a persisted `reports` row.
        return $this->{$method}();
    }

    /**
     * Reflection-style fan-out used by the CLI export. The concrete method name
     * is computed, then invoked via call_user_func.
     */
    public function export(string $format): string
    {
        $callable = [$this, 'exportTo' . ucfirst($format)];

        return (string) call_user_func($callable);
    }

    /**
     * LIVE_TRAP (db-driven-dispatch): reachable only via run('monthlyRevenue')
     * where the literal lives in a seeded DB row, never in PHP source.
     */
    public function monthlyRevenue(): array
    {
        return ['kind' => 'monthly_revenue', 'currency' => 'EUR'];
    }

    /**
     * LIVE_TRAP (db-driven-dispatch): reachable only via run('churnReport').
     */
    public function churnReport(): array
    {
        return ['kind' => 'churn'];
    }

    /**
     * LIVE_TRAP (reflection-dispatch): reached only via call_user_func from
     * export('csv') -> 'exportToCsv'. No literal "exportToCsv(" call exists.
     */
    public function exportToCsv(): string
    {
        return "id,amount\n1,100\n";
    }

    /**
     * LIVE_TRAP (test-only): referenced ONLY from tests/Feature/LegacyReportTest.php.
     * In production code it has zero call sites, but it is covered (and thus
     * load-bearing) for the test suite, so it must NOT be deleted.
     */
    public function legacyTotals(): int
    {
        return 42;
    }
}
