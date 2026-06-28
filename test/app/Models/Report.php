<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * Each row stores the NAME of the ReportBuilder method to run in its `method`
 * column. That string is the only thing that keeps ReportBuilder::monthlyRevenue
 * (etc.) alive -> DB-driven dispatch.
 */
class Report extends Model
{
    protected $fillable = ['name', 'method'];
}
