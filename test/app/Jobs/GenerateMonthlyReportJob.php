<?php

namespace App\Jobs;

/**
 * NOVEL TRAP (job-class-in-json-config): this queued job is never referenced by
 * any PHP `dispatch(...)` / `::class` in source. It is scheduled purely by the
 * fully-qualified class STRING stored in config/schedule.json. The scheduler
 * reads that JSON, resolves the class, and calls handle().
 */
class GenerateMonthlyReportJob
{
    /**
     * LIVE_TRAP (job-class-in-json-config): invoked by the scheduler after
     * resolving the class name from JSON.
     */
    public function handle(): void
    {
        // build + store the monthly report
    }
}
