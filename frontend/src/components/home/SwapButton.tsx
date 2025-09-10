"use client";
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface SwapButtonProps {
  /** Controlled checked state */
  checked?: boolean;
  /** Default checked state for uncontrolled usage */
  defaultChecked?: boolean;
  /** Callback fired when the toggle state changes */
  onChange?: (checked: boolean) => void;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Age verified state */
  onAgeVerified?: (isOpen: boolean) => void;
}

const sizeConfig = {
  sm: {
    container: 'w-16 h-8',
    thumb: 'w-6 h-6',
    icon: 'w-4 h-4',
    translate: 'translate-x-8'
  },
  md: {
    container: 'w-20 h-10',
    thumb: 'w-8 h-8',
    icon: 'w-5 h-5',
    translate: 'translate-x-10'
  },
  lg: {
    container: 'w-24 h-12',
    thumb: 'w-10 h-10',
    icon: 'w-6 h-6',
    translate: 'translate-x-12'
  }
};

// Safe Mode Icon - Shield with sparkle
const SafeIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" className={className}>
    <defs>
      <linearGradient id="safeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#10b981" />
        <stop offset="100%" stopColor="#059669" />
      </linearGradient>
    </defs>
    <motion.path
      d="M12 2L3 7V12C3 16.55 6.84 20.74 12 22C17.16 20.74 21 16.55 21 12V7L12 2Z"
      fill="url(#safeGradient)"
      initial={{ scale: 0.9 }}
      animate={{ 
        scale: [0.9, 1, 0.9],
        opacity: [0.8, 1, 0.8]
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
    <motion.circle
      cx="9"
      cy="9"
      r="1"
      fill="white"
      initial={{ opacity: 0, scale: 0 }}
      animate={{ 
        opacity: [0, 1, 0],
        scale: [0, 1, 0]
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        delay: 0.5
      }}
    />
    <motion.circle
      cx="15"
      cy="13"
      r="0.5"
      fill="white"
      initial={{ opacity: 0, scale: 0 }}
      animate={{ 
        opacity: [0, 1, 0],
        scale: [0, 1, 0]
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        delay: 1
      }}
    />
  </svg>
);

// Adults Mode Icon - Flame with flicker
const AdultsIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="none" className={className}>
    <defs>
      <linearGradient id="flameGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#f97316" />
        <stop offset="50%" stopColor="#dc2626" />
        <stop offset="100%" stopColor="#991b1b" />
      </linearGradient>
      <filter id="glow">
        <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
        <feMerge> 
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <motion.path
      d="M12 2C13.1 6.1 17.5 7 17.5 12.5C17.5 16.6 15.1 20 12 20C8.9 20 6.5 16.6 6.5 12.5C6.5 7 10.9 6.1 12 2Z"
      fill="url(#flameGradient)"
      filter="url(#glow)"
      animate={{ 
        scale: [1, 1.05, 0.98, 1.02, 1],
        opacity: [0.9, 1, 0.85, 1, 0.9]
      }}
      transition={{
        duration: 0.8,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
    <motion.ellipse
      cx="12"
      cy="15"
      rx="3"
      ry="4"
      fill="#fbbf24"
      opacity="0.7"
      animate={{ 
        scale: [0.9, 1.1, 0.95, 1.05, 0.9],
        opacity: [0.5, 0.8, 0.6, 0.7, 0.5]
      }}
      transition={{
        duration: 0.6,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  </svg>
);

export const SwapButton: React.FC<SwapButtonProps> = ({
  checked,
  defaultChecked = false,
  onChange,
  size = 'md',
  className,
  disabled = false,
  onAgeVerified 
}) => {
  const [internalChecked, setInternalChecked] = useState(defaultChecked);
  
  const isControlled = checked !== undefined;
  const isChecked = isControlled ? checked : internalChecked;
  
  const config = sizeConfig[size];
  
  const handleToggle = () => {
    if (disabled) return;
    
    // If switching to adults mode (checked = true) and age not verified
    if (!isChecked && !localStorage.getItem('age_verified')) {
        onAgeVerified?.(true);
        return;
    }
    
    const newChecked = !isChecked;
    
    if (!isControlled) {
      setInternalChecked(newChecked);
    }
    
    onChange?.(newChecked);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Toggle Switch */}
      <button
        type="button"
        role="switch"
        aria-checked={isChecked}
        aria-label={`Switch to ${isChecked ? 'Safe' : 'Adults'} mode`}
        disabled={disabled}
        onClick={handleToggle}
        className={cn(
          // Base container styling
          config.container,
          'relative rounded-full p-1 transition-all duration-300 ease-out',
          'focus:outline-none focus:ring-4 focus:ring-blue-200/50',
          'min-h-[44px] min-w-[44px] md:min-h-0 md:min-w-0', // Larger tap target on mobile
          
          // Liquid glass effect
          'backdrop-blur-xl bg-white/20 border border-white/30',
          'shadow-lg shadow-black/10',
          
          // Hover and active states
          !disabled && 'hover:bg-white/30 hover:shadow-xl hover:shadow-black/20',
          !disabled && 'active:scale-95',
          
          // Disabled state
          disabled && 'opacity-50 cursor-not-allowed',
          
          // Dark mode support
          'dark:bg-black/20 dark:border-white/20 dark:hover:bg-black/30',
          
          className
        )}
        style={{
          backdropFilter: 'blur(16px)',
          background: isChecked 
            ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(185, 28, 28, 0.25) 100%)'
            : 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%)'
        }}
      >
        {/* Animated Thumb */}
        <motion.div
          className={cn(
            config.thumb,
            'rounded-full shadow-lg flex items-center justify-center',
            'backdrop-blur-sm bg-white/80 border border-white/50',
            'dark:bg-white/90'
          )}
          animate={{
            x: isChecked ? `calc(100% + 4px)` : 0,
          }}
          transition={{
            type: "spring",
            stiffness: 500,
            damping: 35,
            mass: 0.8
          }}
          style={{
            boxShadow: isChecked 
              ? '0 4px 12px rgba(239, 68, 68, 0.3), 0 2px 4px rgba(0, 0, 0, 0.1)'
              : '0 4px 12px rgba(16, 185, 129, 0.3), 0 2px 4px rgba(0, 0, 0, 0.1)'
          }}
        >
          {/* Icon with crossfade animation */}
          <AnimatePresence mode="wait">
            {isChecked ? (
              <motion.div
                key="adults"
                initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
                animate={{ opacity: 1, scale: 1, rotate: 0 }}
                exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="flex items-center justify-center"
              >
                <AdultsIcon className={config.icon} />
              </motion.div>
            ) : (
              <motion.div
                key="safe"
                initial={{ opacity: 0, scale: 0.5, rotate: 90 }}
                animate={{ opacity: 1, scale: 1, rotate: 0 }}
                exit={{ opacity: 0, scale: 0.5, rotate: -90 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="flex items-center justify-center"
              >
                <SafeIcon className={config.icon} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
        
        {/* Glass reflection effect */}
        <div 
          className="absolute inset-0 rounded-full opacity-40 pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.4) 0%, transparent 50%, rgba(255, 255, 255, 0.1) 100%)'
          }}
        />
      </button>
      
      {/* Mode Label */}
      <motion.p
        className="text-sm font-montserrat font-medium text-gray-700 dark:text-gray-300"
        animate={{
          color: isChecked ? '#dc2626' : '#059669'
        }}
        transition={{ duration: 0.2 }}
      >
        {isChecked ? 'Restricted content' : 'Safe Mode'}
      </motion.p>
    </div>
  );
};

export default SwapButton;