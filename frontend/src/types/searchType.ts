export interface Message {
  message_id: number;
  context_text: string;
  message_type: string;
  link: string;
}

export interface SearchResult {
  id: number;
  username: string;
  messages: Message[];
}

export interface SearchResponse {
  data: SearchResult[];
  meta: {
    current_page: number;
    last_page: number;
    per_page: number;
    total: number;
  };
}