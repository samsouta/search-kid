<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;

class Message extends Model
{
    protected $fillable = [
        'telegram_id','channel_id','sender_id','message_type','content_text','media_file_path',
        'views','forwards','replies_count','posted_at'
    ];

    protected $casts = [
        'posted_at' => 'datetime',
        'views' => 'integer',
        'forwards' => 'integer',
        'replies_count' => 'integer',
    ];

    public function channel()
    {
        return $this->belongsTo(Channel::class);
    }

    public function sender()
    {
        return $this->belongsTo(Sender::class);
    }

    public function entities()
    {
        return $this->hasMany(MessageEntity::class);
    }

    public function replies()
    {
        return $this->hasMany(MessageReply::class, 'message_id');
    }
}
