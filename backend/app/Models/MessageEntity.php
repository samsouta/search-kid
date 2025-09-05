<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class MessageEntity extends Model
{
     protected $fillable = ['message_id','entity_type','entity_value'];

    public function message()
    {
        return $this->belongsTo(Message::class);
    }
}
