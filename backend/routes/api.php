<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MessageController;


Route::post('/messages/import', [MessageController::class, 'import']);
Route::get('/messages', [MessageController::class, 'index']);


Route::get('/test', function () {
    return response()->json(['message' => 'API is working in Laravel 12!']);
});
