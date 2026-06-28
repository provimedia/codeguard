@extends('layouts.app')

@section('content')
    <ul>
        @foreach ($posts as $post)
            <li>{{ $post->title }} &mdash; {{ $post->author->full_name }}</li>
        @endforeach
    </ul>
@endsection
