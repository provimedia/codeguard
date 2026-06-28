<?php

namespace App\View\Components;

use Illuminate\View\Component;

/**
 * LIVE_TRAP (blade-component): used only as <x-alert type="..."> in Blade
 * templates. The kebab tag maps to this class by convention; there is no PHP
 * import or `new Alert(` anywhere.
 */
class Alert extends Component
{
    public function __construct(public string $type = 'info')
    {
    }

    /**
     * LIVE_TRAP (blade-component): render() is called by the Blade compiler when
     * <x-alert> is encountered, never from PHP code.
     */
    public function render()
    {
        return view('components.alert');
    }

    /**
     * LIVE_TRAP (blade-component): a public accessor consumed inside the
     * component's own Blade template as {{ $cssClass }} / $alert->cssClass().
     */
    public function cssClass(): string
    {
        return 'alert alert-' . $this->type;
    }
}
