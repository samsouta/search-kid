import { SearchResponse } from '@/types/searchType';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const BaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL


export const searchApi = createApi({
  reducerPath: 'searchApi',
  baseQuery: fetchBaseQuery({ baseUrl: BaseUrl }),
  tagTypes: ['search'],
  endpoints: (builder) => ({
    /**
     * GET search query 
     */
    postSearchQuery: builder.query<SearchResponse, { query: string , page: number , adults: boolean }>({
      query: ({ query , page , adults }) => ({
        url: `messages`,
        method: 'GET',
        params: {
          q: query,
          page,
          adults
        },
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }),
      providesTags: ['search'],
    }),


  }),
})
export const { usePostSearchQueryQuery } = searchApi;
