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
        Schema::create('message_entities', function (Blueprint $table) {
            $table->bigIncrements('id');
            $table->foreignId('message_id')
                ->constrained('messages')
                ->onDelete('cascade');

            $table->string('entity_type');
            $table->string('entity_value');

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('message_entities');
    }
};
