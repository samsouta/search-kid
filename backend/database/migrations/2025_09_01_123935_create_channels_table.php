<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('channels', function (Blueprint $table) {
            $table->id();
            $table->bigInteger('telegram_id')->unique(); 
            $table->string('title'); 
            $table->string('username')->nullable(); 
            $table->string('type'); 
            $table->boolean('is_private')->default(false); 
            $table->text('description')->nullable();
            $table->integer('members_count')->nullable(); 
            $table->string('photo_url')->nullable(); 
            $table->timestamps(); 
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('channels');
    }
};
