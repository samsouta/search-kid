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
        Schema::create('messages', function (Blueprint $table) {
            $table->bigIncrements('id'); 
            $table->bigInteger('telegram_id')->unique();

            // Foreign keys
            $table->unsignedBigInteger('channel_id');
            $table->unsignedBigInteger('sender_id')->nullable();

            $table->string('message_type')->default('text');

            $table->longText('content_text')->nullable();
            $table->string('media_file_path')->nullable();
            $table->integer('views')->nullable();
            $table->integer('forwards')->nullable();
            $table->integer('replies_count')->nullable();
            $table->timestamp('posted_at');

            $table->timestamps();

            // Foreign key constraints
            $table->foreign('channel_id')->references('id')->on('channels')->onDelete('cascade');
            $table->foreign('sender_id')->references('id')->on('senders')->onDelete('set null');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('messages');
    }
};
