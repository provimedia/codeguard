<?php

use App\Http\Controllers\AdminController;
use App\Http\Controllers\PostController;
use Illuminate\Support\Facades\Route;

/*
 * Route table. The controller methods below are reachable ONLY through these
 * registrations -- the two forms a real Laravel app mixes:
 *   - modern tuple form:  [PostController::class, 'show']
 *   - legacy string form: 'PostController@index'
 */

// LIVE_TRAP target: PostController::index via the legacy string form.
Route::get('/posts', 'PostController@index')->name('posts.index');

// LIVE_TRAP target: PostController::show via the tuple form.
Route::get('/posts/{id}', [PostController::class, 'show'])->name('posts.show');

Route::get('/admin', [AdminController::class, 'dashboard'])->name('admin.dashboard');
