<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Channel extends Model
{
    protected $fillable = [
        'telegram_id',
        'title',
        'username',
        'type',
        'is_private',
        'is_adults',
        'description',
        'members_count',
        'photo_url',
    ];

    protected $casts = [
        'is_private' => 'boolean',
        'is_adults'  => 'boolean',
        'members_count' => 'integer',
    ];
    
     public function messages()
    {
        return $this->hasMany(Message::class);
    }
    
}
