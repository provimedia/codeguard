@extends('layouts.app')

@section('content')
    {{-- <x-alert> is the ONLY reference to App\View\Components\Alert. --}}
    <x-alert type="success">Post loaded.</x-alert>

    <article>
        <h1>{{ $post->title }}</h1>

        {{-- $post->excerpt is the magic accessor getExcerptAttribute(). --}}
        <p class="excerpt">{{ $post->excerpt }}</p>

        {{-- $post->author->full_name is the magic accessor getFullNameAttribute(). --}}
        <span class="byline">by {{ $post->author->full_name }}</span>

        {{-- $post->author->initials is getInitialsAttribute(). --}}
        <span class="avatar">{{ $post->author->initials }}</span>
    </article>
@endsection
