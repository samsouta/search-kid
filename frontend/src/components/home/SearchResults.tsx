import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { SearchResult } from '@/types/searchType';
import Pagination from './Pagination';
import Image from 'next/image';

interface SearchResultsProps {
  results: SearchResult[];
  isSearching: boolean;
  isLoading: boolean;
  searchQuery: string;
  totalPages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({ results, isSearching, isLoading, searchQuery, totalPages, currentPage, onPageChange }) => {
  const [messagePageIndex, setMessagePageIndex] = useState<Record<string, number>>({});

  // Show loading state
  if (isSearching || isLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="grid gap-6 md:gap-8">
          {[...Array(3)].map((_, index) => (
            <div key={index} className="animate-pulse">
              <div className="backdrop-blur-md bg-white/5 rounded-2xl border border-white/10 p-6 md:p-8">
                <div className="h-6 bg-white/20 rounded-lg w-3/4 mb-4"></div>
                <div className="h-4 bg-white/10 rounded-lg w-1/2 mb-3"></div>
                <div className="h-4 bg-white/10 rounded-lg w-full mb-2"></div>
                <div className="h-4 bg-white/10 rounded-lg w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Initial state - no search performed yet
  if (!searchQuery) {
    return (
      <div className="max-w-4xl mx-auto text-center">
        <div className="backdrop-blur-md bg-white/5 rounded-2xl border border-white/10 p-12 md:p-16">
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-400/20 to-purple-400/20 flex items-center justify-center">
            <Search className="w-12 h-12 text-white/40" />
          </div>
          <h3 className="text-xl md:text-2xl font-semibold text-white/80 mb-4">
            Start your search
          </h3>
          <p className="text-white/60 max-w-md mx-auto">
            Enter a keyword or phrase in the search bar above to discover amazing content
          </p>
        </div>
      </div>
    );
  }

  // No results found for search query
  if (results.length === 0) {
    return (
      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
        <div className="backdrop-blur-md bg-white/5 rounded-2xl border border-white/10 p-8 md:p-12 relative min-h-[500px] overflow-hidden">
          {/* Background image with overlay */}
          <div className="absolute inset-0 z-0">
            <Image
              src="/images/404/not-found.png"
              alt="No results illustration"
              fill
              priority
              className=""
              style={{ objectFit: "cover" }}
            />
          </div>
        </div>
      </div>
    );
  }

  const handleNextMessages = (resultId: string) => {
    setMessagePageIndex(prev => ({
      ...prev,
      [resultId]: (prev[resultId] || 0) + 1
    }));
  };

  const handlePreviousMessages = (resultId: string) => {
    setMessagePageIndex(prev => ({
      ...prev,
      [resultId]: Math.max((prev[resultId] || 0) - 1, 0)
    }));
  };

  // Display search results
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 md:mb-8">
        <p className="text-white/70 text-sm md:text-base">
          Found {results.length.toLocaleString()} result{results.length === 1 ? '' : 's'} for &quot;{searchQuery}&quot;
        </p>
      </div>

      {/* // Card  */}
      <div className="grid grid-cols-1 gap-6 md:gap-8">
        {results.map((result, index) => {
          const currentPageIndex = messagePageIndex[result.id || index.toString()] || 0;
          const messagesPerPage = 5;
          const startIndex = currentPageIndex * messagesPerPage;
          const displayedMessages = result.messages?.slice(startIndex, startIndex + messagesPerPage);
          const totalMessagePages = Math.ceil((result.messages?.length || 0) / messagesPerPage);
          const hasNextPage = currentPageIndex < totalMessagePages - 1;
          const hasPreviousPage = currentPageIndex > 0;

          return (
            <div
              key={result.id || index}
              className="group backdrop-blur-lg bg-white/5 hover:bg-white/10 rounded-2xl border border-white/10 hover:border-white/20 p-6 transition-all duration-300 hover:shadow-[0_0_30px_rgba(255,255,255,0.1)]"
            >
              {/* Channel Header */}
              <div className="flex items-center gap-4 mb-4 pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-semibold text-white/90 group-hover:text-white transition-colors">
                    {result.username || 'Unknown Channel'}
                  </h3>
                  <p className="text-sm text-white/60">
                    {result?.messages?.length || 0} messages found
                  </p>
                </div>
              </div>

              {/* Messages List */}
              <div className="space-y-4">
                {displayedMessages?.map((message, msgIndex) => (
                  <div
                    key={msgIndex}
                    className="backdrop-blur-sm bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all duration-200"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white/90">
                            {message?.message_type || 'Unknown'}
                          </span>
                        </div>
                        <a
                          href={message?.link || ''}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-white/70 hover:text-white/90 underline decoration-white/30 hover:decoration-white/60 transition-all duration-200 break-words hover:bg-white/5 rounded px-1"
                          title={message?.context_text || ''}
                        >
                          {message?.context_text?.length > 100
                            ? `${message.context_text.slice(0, 100)}...`
                            : message?.context_text}
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Navigation Buttons */}
              <div className="mt-4 flex justify-center gap-4">
                {hasPreviousPage && (
                  <button
                    onClick={() => handlePreviousMessages(result.id.toString() || index.toString())}
                    className="px-4 py-2 text-sm text-white/70 hover:text-white/90 bg-white/5 hover:bg-white/10 rounded-lg transition-all duration-200"
                  >
                    Previous Messages
                  </button>
                )}
                {hasNextPage && (
                  <button
                    onClick={() => handleNextMessages(result.id.toString() || index.toString())}
                    className="px-4 py-2 text-sm text-white/70 hover:text-white/90 bg-white/5 hover:bg-white/10 rounded-lg transition-all duration-200"
                  >
                    Next Messages
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
};

export default SearchResults;