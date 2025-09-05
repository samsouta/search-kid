import React, { useState } from 'react';
import { Search, Loader } from 'lucide-react';

interface SearchBarProps {
  isSearching: boolean;
  onSearch: (query: string) => void;
  setIsModalOpen: (isOpen: boolean) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ isSearching, onSearch, setIsModalOpen }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState("");

  /**
   * Handle form submission
   */
  const handleSubmit = () => {
    if (!localStorage.getItem('terms_of_service')) {
      setIsModalOpen(true);
      return;
    }
    if (searchQuery.trim()) {
      onSearch(searchQuery);
    }

  };

  return (
    <div className="relative group w-full max-w-[95vw] mx-auto">
      {error && (
        <p className="text-red-400 text-sm mt-2">{error}</p>
      )}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-25 group-hover:opacity-40 transition-opacity duration-300"></div>
      <div className="relative backdrop-blur-md bg-white/10 rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
        <div className="flex flex-wrap sm:flex-nowrap items-center p-3 sm:p-4 md:p-6 gap-2 sm:gap-4">
          <div className="flex-shrink-0">
            {isSearching ? (
              <Loader className="w-5 h-5 sm:w-6 sm:h-6 text-white/60 animate-spin" />
            ) : (
              <Search className="w-5 h-5 sm:w-6 sm:h-6 text-white/60" />
            )}
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              const value = e.target.value;
              
              if (value.length > 80) {
                setError("Maximum 80 characters allowed!");
              } else {
                setError("");
                setSearchQuery(value);
              }
            }}
            placeholder="Search for anything..."
            className="flex-1 min-w-0 bg-transparent text-white placeholder-white/50 text-base sm:text-lg md:text-xl focus:outline-none font-medium"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="flex-shrink-0 text-white/40 hover:text-white/70 transition-colors duration-200"
            >
              <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
                ×
              </div>
            </button>
          )}
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isSearching}
            className="w-full sm:w-auto flex-shrink-0 px-3 sm:px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors duration-200 text-sm sm:text-base"
          >
            Search
          </button>
        </div>

        {/* Subtle inner glow effect */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>
      </div>
    </div>
  );
};

export default SearchBar;