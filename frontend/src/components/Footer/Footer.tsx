import React from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'

const Footer = () => {
  return (
    <footer className=" text-white py-8 px-4 md:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-6 md:mb-0">
            <h3 className="font-montserrat text-xl font-semibold">SearchKid</h3>
          </div>
          
          <div
            
          >
            <Link
              href="/terms-of-service"
              className="font-lora text-base hover:text-blue-400 transition-colors duration-300 relative group"
            >
              <span className="inline-block">
                Terms of Service
                <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-400 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300"></span>
              </span>
            </Link>
          </div>
        </div>
        
        <div className="mt-8 text-center text-sm font-montserrat text-gray-400">
          <p>&copy; {new Date().getFullYear()} SearchKid. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer