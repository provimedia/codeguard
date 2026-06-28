<?php

namespace App\Enums;

enum PayoutStatus: string
{
    case Pending = 'pending';
    case Settled = 'settled';
    case Failed = 'failed';
}
