<?php

namespace App\Http\Controllers;

use Stichoza\GoogleTranslate\GoogleTranslate;
use Illuminate\Support\Facades\Log;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use App\Models\Channel;
use App\Models\Sender;
use App\Models\Message;
use App\Models\MessageEntity;

use function PHPSTORM_META\map;

class MessageController extends Controller
{
    /**
     * Import messages from Telegram
     */
    public function import(Request $request)
    {
        $token = $request->bearerToken();
        if (!$token || $token !== env('IMPORT_TOKEN')) {
            return response()->json(['error' => 'Unauthorized'], 401);
        }

        $payload = $request->all();
        if (empty($payload)) {
            return response()->json(['error' => 'Empty payload'], 400);
        }

        // Normalize: accept single object or array
        if (array_keys($payload) !== range(0, count($payload) - 1)) {
            $payload = [$payload];
        }

        $created = 0;
        $updated = 0;
        $skipped = 0;

        foreach ($payload as $item) {
            if (empty($item['channel']['telegram_id']) || empty($item['message']['telegram_id'])) {
                $skipped++;
                continue;
            }

            DB::beginTransaction();
            try {
                // --- Upsert channel ---
                $channel = Channel::updateOrCreate(
                    ['telegram_id' => $item['channel']['telegram_id']],
                    [
                        'title'         => $item['channel']['title'] ?? null,
                        'username'      => $item['channel']['username'] ?? null,
                        'is_private'    => $item['channel']['is_private'] ?? false,
                        'is_adults'    => (bool)($item['channel']['is_adults'] ?? false),
                        'type'          => $item['channel']['type'] ?? 'channel',
                        'description'   => $item['channel']['description'] ?? null,
                        'members_count' => $item['channel']['members_count'] ?? null,
                        'photo_url'     => $item['channel']['photo_url'] ?? null,
                    ]
                );

                // --- Upsert sender ---
                $sender = null;
                if (!empty($item['sender']['telegram_id'])) {
                    $sender = Sender::updateOrCreate(
                        ['telegram_id' => $item['sender']['telegram_id']],
                        [
                            'username'     => $item['sender']['username'] ?? null,
                            'display_name' => $item['sender']['display_name'] ?? null,
                            'is_bot'       => $item['sender']['is_bot'] ?? false,
                            'photo_url'    => $item['sender']['photo_url'] ?? null,
                        ]
                    );
                }

                // --- Upsert message ---
                $msgData = $item['message'];
                $message = Message::updateOrCreate(
                    [
                        'telegram_id' => $msgData['telegram_id'],
                        'channel_id'  => $channel->id,
                    ],
                    [
                        'sender_id'       => $sender?->id,
                        'message_type'    => $msgData['message_type'] ?? 'text',
                        'content_text'    => $msgData['content_text'] ?? null,
                        'media_file_path' => $msgData['media_file_path'] ?? null,
                        'views'           => $msgData['views'] ?? 0,
                        'forwards'        => $msgData['forwards'] ?? 0,
                        'replies_count'   => $msgData['replies_count'] ?? 0,
                        'posted_at'       => $msgData['posted_at'] ?? null,
                    ]
                );

                // --- Entities ---
                if (!empty($item['entities'])) {
                    MessageEntity::where('message_id', $message->id)->delete();
                    foreach ($item['entities'] as $ent) {
                        if (empty($ent['entity_type']) || empty($ent['entity_value'])) continue;
                        MessageEntity::create([
                            'message_id'   => $message->id,
                            'entity_type'  => $ent['entity_type'],
                            'entity_value' => $ent['entity_value'],
                        ]);
                    }
                }

                DB::commit();

                // --- Stats ---
                if ($message->wasRecentlyCreated) {
                    $created++;
                } elseif ($message->wasChanged()) {
                    $updated++;
                } else {
                    $skipped++;
                }
            } catch (\Throwable $e) {
                DB::rollBack();
                $skipped++;
                \Log::error('Message import error: ' . $e->getMessage(), ['item' => $item]);
            }
        }

        return response()->json([
            'status'   => 'ok',
            'created'  => $created,
            'updated'  => $updated,
            'skipped'  => $skipped,
        ]);
    }

    /**
     * Search messages (GET /api/messages?q=...)
     */
    public function index(Request $request)
    {
        $q = trim($request->query('q', ''));
        if ($q === '') {
            return response()->json(['error' => 'Missing q parameter'], 400);
        }

        $adults = $request->has('adults')
            ? filter_var($request->query('adults'), FILTER_VALIDATE_BOOLEAN)
            : null;

        $terms = $this->buildSearchTerms($q);

        // 1) Get all matching channel IDs first
        $channelIds = Message::query()
            ->when($adults !== null, function ($query) use ($adults) {
                $query->whereHas('channel', function ($cQ) use ($adults) {
                    $cQ->where('is_adults', $adults);
                });
            })
            ->where(function ($mQ) use ($terms) {
                $mQ->where(function ($q) use ($terms) {
                    foreach ($terms as $t) {
                        $q->orWhereRaw('content_text ILIKE ?', ["%{$t}%"]);
                    }
                })->orWhereHas('entities', function ($eQ) use ($terms) {
                    $eQ->where(function ($q2) use ($terms) {
                        foreach ($terms as $t) {
                            $q2->orWhereRaw('entity_value ILIKE ?', ["%{$t}%"]);
                        }
                    });
                });
            })
            ->pluck('channel_id')
            ->unique();

        // 2) Paginate channels
        $perPage = (int) $request->query('per_page', 10);
        $currentPage = (int) $request->query('page', 1);

        $channelsPaginator = Channel::whereIn('id', $channelIds)
            ->orderBy('id', 'desc')
            ->paginate($perPage, ['*'], 'page', $currentPage);

        // 3) Fetch messages for only those paginated channels
        $messages = Message::with('channel')
            ->whereIn('channel_id', $channelsPaginator->pluck('id'))
            ->where(function ($mQ) use ($terms) {
                $mQ->where(function ($q) use ($terms) {
                    foreach ($terms as $t) {
                        $q->orWhereRaw('content_text ILIKE ?', ["%{$t}%"]);
                    }
                })->orWhereHas('entities', function ($eQ) use ($terms) {
                    $eQ->where(function ($q2) use ($terms) {
                        foreach ($terms as $t) {
                            $q2->orWhereRaw('entity_value ILIKE ?', ["%{$t}%"]);
                        }
                    });
                });
            })
            ->orderBy('posted_at', 'desc')
            ->get();

        // 4) Group messages by channel
        $data = $messages
            ->groupBy(fn($m) => $m->channel->id)
            ->map(function ($msgs, $channelId) {
                $channel = $msgs->first()->channel;

                return [
                    'id'       => $channel->id,
                    'username' => $channel->username,
                    'messages' => $msgs->map(function ($msg) {
                        return [
                            'message_id'   => $msg->id,
                            'context_text' => $msg->content_text,
                            'message_type' => $msg->message_type,
                            'link'         => $msg->media_file_path,
                        ];
                    })->values(),
                ];
            })
            ->values();

        // 5) Return with meta
        return response()->json([
            'data' => $data,
            'meta' => [
                'current_page' => $channelsPaginator->currentPage(),
                'last_page'    => $channelsPaginator->lastPage(),
                'per_page'     => $channelsPaginator->perPage(),
                'total'        => $channelsPaginator->total(),
            ],
        ]);
    }


    /**
     * Build search terms (original + translations)
     */
    private function buildSearchTerms(string $q): array
    {
        $variants = [trim($q)];

        // Detect Myanmar text
        $isMyanmar = preg_match('/[\p{Myanmar}]/u', $q);

        // If input is Myanmar, skip translation completely
        if ($isMyanmar) {
            \Log::info("No translation needed for Myanmar input: '{$q}'");
            return $this->uniqueNonEmpty($variants);
        }

        // Otherwise, translate to English + Chinese
        try {
            $tr = new GoogleTranslate();

            $targets = ['en', 'zh'];
            foreach ($targets as $target) {
                $tr->setTarget($target);
                $translated = trim($tr->translate($q));

                if ($translated && $translated !== $q) {
                    \Log::info("Translated '{$q}' → '{$translated}' for target {$target}");
                    $variants[] = $translated;
                }
            }
        } catch (\Throwable $e) {
            \Log::warning('Search translation skipped: ' . $e->getMessage());
        }

        return $this->uniqueNonEmpty($variants);
    }

    /**
     * Remove duplicates, empties, and reindex array
     */
    private function uniqueNonEmpty(array $arr): array
    {
        $arr = array_map('trim', $arr);
        $arr = array_filter($arr, fn($v) => $v !== '');
        $arr = array_values(array_unique($arr));
        return $arr;
    }
}
