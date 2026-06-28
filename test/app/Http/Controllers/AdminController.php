<?php

namespace App\Http\Controllers;

use App\Enums\PayoutStatus;
use App\Models\Report;
use App\Services\PayoutProcessor;
use App\Services\ReportBuilder;
use App\Support\Money;
use Illuminate\Support\Str;

/**
 * Dashboard glue. This is where the runtime dispatchers are actually *invoked*
 * with runtime values -- but note that the concrete target symbols
 * (monthlyRevenue, exportToCsv, handleSettled, renderEur, slugifyTitle) never
 * appear as literal call sites here. They are reached only through the string /
 * enum / macro indirection.
 */
class AdminController extends Controller
{
    public function dashboard(ReportBuilder $builder, PayoutProcessor $payouts)
    {
        // DB-driven dispatch: the method name comes from a persisted row.
        $report = Report::query()->firstOrFail();
        $data = $builder->run($report->method);

        // Reflection-style dispatch: 'csv' -> exportToCsv via call_user_func.
        $csv = $builder->export('csv');

        // Enum-driven dispatch: case name -> handle<Case>().
        $state = $payouts->process(PayoutStatus::Settled);

        // Magic __call routing: ->eur() -> renderEur().
        $price = Money::of(1999)->eur();

        // Str macro: registered at runtime, called by macro name.
        $slug = Str::slugifyTitle($report->name);

        return view('admin.dashboard', compact('data', 'csv', 'state', 'price', 'slug'));
    }
}
