import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
    currentPage,
    totalPages,
    onPageChange,
}) => {
    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxVisiblePages = 7;
        const showEllipsis = totalPages > maxVisiblePages;

        if (!showEllipsis) {
            // Show all pages if total is 7 or less
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Smart pagination with ellipsis
            const leftSide = 2;
            const rightSide = 2;

            if (currentPage <= leftSide + 2) {
                // Near beginning
                for (let i = 1; i <= leftSide + 2; i++) pages.push(i);
                pages.push('...');
                for (let i = totalPages - 1; i <= totalPages; i++) pages.push(i);
            } else if (currentPage >= totalPages - (rightSide + 1)) {
                // Near end
                pages.push(1, 2, '...');
                for (let i = totalPages - (rightSide + 2); i <= totalPages; i++) pages.push(i);
            } else {
                // Middle
                pages.push(1, '...');
                for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
                pages.push('...', totalPages);
            }
        }

        return pages;
    };

    const handlePageClick = (page: number | string) => {
        if (typeof page === 'number' && page !== currentPage) {
            onPageChange(Math.min(Math.max(1, page), totalPages));
        }
        // smooth scroll to top
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    const canGoPrevious = currentPage > 1;
    const canGoNext = currentPage < totalPages;

    return (
        <nav className="flex items-center justify-center space-x-2 mt-8" aria-label="Pagination">
            {/* Previous Button */}
            <button
                onClick={() => canGoPrevious && handlePageClick(currentPage - 1)}
                disabled={!canGoPrevious}
                aria-label="Previous page"
                className={`
          flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
          ${canGoPrevious
                        ? 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                        : 'bg-gray-100/50 text-gray-400 cursor-not-allowed border border-gray-200/50'
                    }
        `}
            >
                <ChevronLeft className="w-4 h-4" />
                Previous
            </button>

            {/* Page Numbers */}
            <div className="flex items-center space-x-1" role="group">
                {getPageNumbers().map((page, index) => {
                    if (page === '...') {
                        return (
                            <span
                                key={`ellipsis-${index}`}
                                className="px-3 py-2 text-gray-500 text-sm"
                                aria-hidden="true"
                            >
                                &#8230;
                            </span>
                        );
                    }

                    const isActive = page === currentPage;
                    return (
                        <button
                            key={`page-${page}`}
                            onClick={() => handlePageClick(page)}
                            aria-current={isActive ? 'page' : undefined}
                            aria-label={`Page ${page}`}
                            className={`
                px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${isActive
                                    ? 'bg-blue-500 text-white shadow-lg border border-blue-600'
                                    : 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                                }
              `}
                        >
                            {page}
                        </button>
                    );
                })}
            </div>

            {/* Next Button */}
            <button
                onClick={() => canGoNext && handlePageClick(currentPage + 1)}
                disabled={!canGoNext}
                aria-label="Next page"
                className={`
          flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
          ${canGoNext
                        ? 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                        : 'bg-gray-100/50 text-gray-400 cursor-not-allowed border border-gray-200/50'
                    }
        `}
            >
                Next
                <ChevronRight className="w-4 h-4" />
            </button>
        </nav>
    );
};

export default Pagination;