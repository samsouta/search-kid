import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AgeVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (isAdult: boolean) => void;
}

const AgeVerificationModal: React.FC<AgeVerificationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
}) => {
  const handleYes = () => {
    localStorage.setItem('age_verified', 'true');
    onConfirm(true);
    onClose();
  };

  const handleNo = () => {
    onConfirm(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          >
            {/* Modal Container */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ 
                duration: 0.4,
                type: "spring",
                stiffness: 300,
                damping: 30
              }}
              className="relative w-full max-w-md mx-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Glass Modal */}
              <div className="relative bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-black/20">
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-white/5 to-transparent rounded-3xl pointer-events-none" />
                
                {/* Close Button */}
                {/* <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-white/80 hover:text-white hover:bg-white/20 transition-all duration-200 hover:scale-110"
                >
                  <X size={20} />
                </button> */}

                {/* Content */}
                <div className="relative z-10 text-center">
                  {/* Title */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">
                      Age Verification
                    </h2>
                    <div className="w-16 h-1 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full mx-auto mb-6"></div>
                  </motion.div>

                  {/* Question */}
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-lg sm:text-xl text-white/90 mb-8 leading-relaxed"
                  >
                    Are you above 18 years old?
                  </motion.p>

                  {/* Buttons */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="space-y-4 mb-6"
                  >
                    {/* Yes Button */}
                    <button
                      onClick={handleYes}
                      className="w-full py-4 px-6 bg-gradient-to-r from-blue-500/30 to-purple-500/30 backdrop-blur-sm border border-blue-400/50 rounded-2xl text-white font-semibold text-lg transition-all duration-300 hover:from-blue-500/40 hover:to-purple-500/40 hover:border-blue-300/70 hover:shadow-lg hover:shadow-blue-500/25 hover:scale-[1.02] active:scale-[0.98] group"
                    >
                      <span className="relative z-10">Yes, I&apos;m 18+</span>
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    </button>

                    {/* No Button */}
                    <button
                      onClick={handleNo}
                      className="w-full py-4 px-6 bg-white/5 backdrop-blur-sm border border-white/20 rounded-2xl text-white/80 font-medium text-lg transition-all duration-300 hover:bg-white/10 hover:border-white/30 hover:text-white hover:scale-[1.02] active:scale-[0.98]"
                    >
                      No, I&apos;m under 18
                    </button>
                  </motion.div>

                  {/* Disclaimer */}
                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="text-sm text-white/60 leading-relaxed"
                  >
                    You must be at least 18 years old to enter.
                  </motion.p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default AgeVerificationModal;