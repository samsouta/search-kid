<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class MessageReply extends Model
{
    protected $fillable = ['message_id','reply_to_id'];

    public function message()
    {
        return $this->belongsTo(Message::class, 'message_id');
    }

    public function replyTo()
    {
        return $this->belongsTo(Message::class, 'reply_to_id');
    }
}
