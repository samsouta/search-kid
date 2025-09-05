"use client"
import React, { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import { theme } from '@/styles/theme';
import { usePostSearchQueryQuery } from '@/service/api/searchApi';
import SearchResults from './SearchResults';
import SwapButton from './SwapButton';
import TermsModal from '../UI/Alert/TermsModal';
import AgeVerificationModal from '../UI/Alert/AgeVerificationModal';

const SearchPage: React.FC = () => {
  const [curPage, setCurPage] = useState(1);
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [settingsMode, setSettingsMode] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAgeModalOpen, setIsAgeModalOpen] = useState(false);
  const { data, isLoading, refetch } = usePostSearchQueryQuery({
    query: searchQuery.trim(),
    page: curPage,
    adults: settingsMode,
  });

  useEffect(() => {
    setCurPage(1);
  }, [searchQuery]);

  const handleSearch = (query: string) => {
    const trimmedQuery = query.trim();
    if (trimmedQuery === '') return;

    setIsSearching(true);
    setSearchQuery(trimmedQuery);
    refetch();

    const timer = setTimeout(() => {
      setIsSearching(false);
    }, 1000);

    return () => clearTimeout(timer);
  };

  const handlePageChange = (newPage: number) => {
    setCurPage(newPage);
    refetch();
  };

  const handleAcceptTerms = () => {
    localStorage.setItem('terms_of_service', 'true');
    setIsModalOpen(false);
  };

  const backgroundElements = [
    { position: '-top-40 -right-40', color: 'bg-blue-400', delay: '' },
    { position: '-bottom-40 -left-40', color: 'bg-purple-400', delay: 'delay-1000' },
    { position: 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2', color: 'bg-indigo-400', delay: 'delay-500', size: 'w-96 h-96', opacity: 'opacity-10' }
  ];

  return (
    <main className="min-h-screen bg-transparent relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden">
        {backgroundElements.map((element, index) => (
          <div
            key={index}
            className={`absolute ${element.position} ${element.size || 'w-80 h-80'} ${element.color} rounded-full mix-blend-multiply filter blur-xl ${element.opacity || 'opacity-20'} animate-pulse ${element.delay}`}
          />
        ))}
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 md:py-16 flex flex-col gap-6">
        <header className="text-center space-y-4">
          <div className={theme?.text}>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight">
              Search Something on{' '}
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                SearchKid
              </span>
            </h1>
            <p className={`${theme?.secondaryText} text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mt-4`}>
              what you want to search today ?
            </p>

            {/* Interactive Demo */}
            <section className="py-8">
              <div className="max-w-2xl mx-auto">
                <div >
                  <SwapButton
                    checked={settingsMode}
                    onChange={setSettingsMode}
                    onAgeVerified={setIsAgeModalOpen}
                    size="lg"
                  />
                  <p className={`text-sm font-montserrat text-gray-600 ${settingsMode ? 'text-red-500' : 'text-green-500'}`}>
                    {settingsMode
                      ? 'Parental controls are off!. All content is visible.'
                      : 'Parental controls are on. Unsafe content is hidden.'
                    }
                  </p>
                </div>
              </div>
            </section>
          </div>
        </header>

        <section className="max-w-3xl mx-auto w-full">
          <SearchBar
            isSearching={isLoading}
            onSearch={handleSearch}
            setIsModalOpen={setIsModalOpen}
          />
          <p className="text-sm md:text-base text-gray-400 mt-2 font-montserrat">
            💡 Tip: Use short keywords for better results (e.g., <em>"avatar"</em> instead of <em>"best avatar movie scenes 2024"</em>).
          </p>
        </section>

        <section className="w-full">
          <SearchResults
            results={data?.data || []}
            isSearching={isLoading}
            isLoading={isSearching}
            searchQuery={searchQuery}
            totalPages={data?.meta?.last_page || 0}
            currentPage={curPage}
            onPageChange={handlePageChange}
          />
        </section>
      </div>

      {/* Tos */}
      <TermsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAccept={handleAcceptTerms}
      />

      {/* Age Verification Modal */}
      <AgeVerificationModal
        isOpen={isAgeModalOpen}
        onClose={() => setIsAgeModalOpen(false)}
        onConfirm={() => setIsAgeModalOpen(false)}
      />
    </main>
  );
};

export default SearchPage;