import React from 'react';
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
}

const Pagination: React.FC<PaginationProps> = ({
    currentPage,
    totalPages,
    onPageChange,
    disabled = false,
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
        // Prevent clicks when disabled or loading
        if (disabled || typeof page !== 'number' || page === currentPage) {
            return;
        }
        
        const validPage = Math.min(Math.max(1, page), totalPages);
        onPageChange(validPage);
        
        // Smooth scroll to top
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    const canGoPrevious = currentPage > 1 && !disabled;
    const canGoNext = currentPage < totalPages && !disabled;

    return (
        <nav 
            className={`flex items-center justify-center space-x-2 mt-8 ${disabled ? 'pointer-events-none' : ''}`} 
            aria-label="Pagination"
        >
            {/* Previous Button */}
            <button
                onClick={() => handlePageClick(currentPage - 1)}
                disabled={!canGoPrevious || disabled}
                aria-label="Previous page"
                className={`
                    flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${canGoPrevious && !disabled
                        ? 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                        : 'bg-gray-100/50 text-gray-400 cursor-not-allowed border border-gray-200/50'
                    }
                    ${disabled ? 'opacity-60' : ''}
                `}
            >
                {disabled ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <ChevronLeft className="w-4 h-4" />
                )}
                Previous
            </button>

            {/* Page Numbers */}
            <div className="flex items-center space-x-1" role="group">
                {getPageNumbers().map((page, index) => {
                    if (page === '...') {
                        return (
                            <span
                                key={`ellipsis-${index}`}
                                className={`px-3 py-2 text-gray-500 text-sm ${disabled ? 'opacity-60' : ''}`}
                                aria-hidden="true"
                            >
                                &#8230;
                            </span>
                        );
                    }

                    const isActive = page === currentPage;
                    const isDisabledOrLoading = disabled || isActive;
                    
                    return (
                        <button
                            key={`page-${page}`}
                            onClick={() => handlePageClick(page)}
                            disabled={isDisabledOrLoading}
                            aria-current={isActive ? 'page' : undefined}
                            aria-label={`Page ${page}`}
                            className={`
                                px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative
                                ${isActive
                                    ? 'bg-blue-500 text-white shadow-lg border border-blue-600'
                                    : disabled
                                        ? 'bg-white/20 text-gray-400 cursor-not-allowed border border-white/20 opacity-60'
                                        : 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                                }
                                ${disabled && isActive ? 'opacity-80' : ''}
                            `}
                        >
                            {/* Show loading spinner on current page when disabled */}
                            {disabled && isActive ? (
                                <div className="flex items-center gap-1">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    {page}
                                </div>
                            ) : (
                                page
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Next Button */}
            <button
                onClick={() => handlePageClick(currentPage + 1)}
                disabled={!canGoNext || disabled}
                aria-label="Next page"
                className={`
                    flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${canGoNext && !disabled
                        ? 'bg-white/30 backdrop-blur-md text-gray-700 hover:bg-white/50 hover:shadow-md border border-white/40'
                        : 'bg-gray-100/50 text-gray-400 cursor-not-allowed border border-gray-200/50'
                    }
                    ${disabled ? 'opacity-60' : ''}
                `}
            >
                Next
                {disabled ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <ChevronRight className="w-4 h-4" />
                )}
            </button>
        </nav>
    );
};

export default Pagination;