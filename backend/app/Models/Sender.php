<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Sender extends Model
{
    
    protected $fillable = [
        'telegram_id','username','display_name','is_bot','photo_url'
    ];

    protected $casts = [
        'is_bot' => 'boolean',
    ];
    
     public function messages()
    {
        return $this->hasMany(Message::class);
    }
}
