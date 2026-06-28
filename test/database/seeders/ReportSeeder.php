<?php

namespace Database\Seeders;

use App\Models\Report;
use Illuminate\Database\Seeder;

/**
 * The `method` values seeded here are plain DATA strings. They are the only
 * thing that keeps ReportBuilder::monthlyRevenue alive (DB-driven dispatch).
 * Note: these are string literals in a data array, NOT call sites.
 */
class ReportSeeder extends Seeder
{
    public function run(): void
    {
        Report::query()->insert([
            ['name' => 'Monthly revenue', 'method' => 'monthlyRevenue'],
            ['name' => 'Customer churn', 'method' => 'churnReport'],
        ]);
    }
}
