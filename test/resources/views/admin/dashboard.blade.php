@extends('layouts.app')

@section('content')
    <pre>{{ json_encode($data) }}</pre>
    <p>{{ $state }} &middot; {{ $price }} &middot; {{ $slug }}</p>
@endsection
