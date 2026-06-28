{{-- $cssClass / cssClass() is consumed here, inside the component's own view. --}}
<div class="{{ $cssClass() }}" role="alert">
    {{ $slot }}
</div>
