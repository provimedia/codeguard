<?php

namespace Tests\Feature;

use App\Services\ReportBuilder;
use PHPUnit\Framework\TestCase;

/**
 * This is the ONLY place that references ReportBuilder::legacyTotals(). It is
 * test-only coverage: deleting legacyTotals would break this test, so the method
 * is NOT dead even though production code never calls it.
 */
class LegacyReportTest extends TestCase
{
    public function test_legacy_totals_returns_fixed_value(): void
    {
        $builder = new ReportBuilder();

        $this->assertSame(42, $builder->legacyTotals());
    }
}
