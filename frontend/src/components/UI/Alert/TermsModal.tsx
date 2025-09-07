import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface TermsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: () => void;
}

const TermsModal: React.FC<TermsModalProps> = ({ isOpen, onClose, onAccept }) => {
  // Handle escape key press
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
  };



  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          {/* Backdrop */}
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="absolute inset-0 bg-black/30 backdrop-blur-lg"
            onClick={onClose}
            transition={{ duration: 0.2 }}
          />

          {/* Modal */}
          <motion.div
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative w-full max-w-md mx-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Glass container */}
            <div className="relative bg-white/10 backdrop-blur-2xl border border-white/30 rounded-3xl shadow-2xl shadow-black/20 overflow-hidden">
              {/* Gradient overlay for glass effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-white/10 to-transparent pointer-events-none" />
              
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2.5 rounded-full bg-white/15 hover:bg-white/25 border border-white/30 transition-all duration-300 hover:scale-110 hover:shadow-lg hover:shadow-white/20 group z-10"
                aria-label="Close modal"
              >
                <X className="w-5 h-5 text-white group-hover:text-white/90 transition-colors" />
              </button>

              {/* Content */}
              <div className="relative p-6 sm:p-8 pt-12">
                {/* Header */}
                <div className="text-center mb-8">
                  <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-blue-400/40 to-purple-600/40 backdrop-blur-sm border border-white/30 flex items-center justify-center transform hover:scale-105 transition-transform duration-300">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-400 to-purple-600 shadow-lg animate-pulse" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-3">
                    Terms of Service
                  </h2>
                  <div className="w-16 h-1 bg-gradient-to-r from-blue-400 to-purple-600 mx-auto rounded-full shadow-lg" />
                </div>

                {/* Message */}
                <div className="text-center mb-10">
                  <p className="text-white/90 text-lg leading-relaxed mb-4">
                    Do you accept our Terms of Service to continue using this website?
                  </p>
                  <a
                    href="/terms-of-service"
                    className="inline-flex items-center text-blue-300 hover:text-blue-200 transition-colors duration-300 text-sm font-medium underline underline-offset-4 hover:underline-offset-8 hover:scale-105 transform"
                  >
                    Read more about our Terms of Service
                  </a>
                </div>

                {/* Buttons */}
                <div className="flex flex-col sm:flex-row gap-4">
                  {/* Accept Button */}
                  <button
                    onClick={onAccept}
                    className="flex-1 relative group overflow-hidden px-8 py-4 rounded-2xl bg-gradient-to-br from-blue-500/90 to-purple-600/90 hover:from-blue-500 hover:to-purple-600 border border-white/30 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98] transform"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-white/30 via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="relative text-white font-semibold text-lg">
                      Accept
                    </span>
                  </button>

                  {/* Decline Button */}
                  <button
                    onClick={onClose}
                    className="flex-1 px-8 py-4 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/30 backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-lg hover:shadow-white/20 active:scale-[0.98] group transform"
                  >
                    <span className="text-white/90 group-hover:text-white font-medium text-lg transition-colors">
                      Decline
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default TermsModal;