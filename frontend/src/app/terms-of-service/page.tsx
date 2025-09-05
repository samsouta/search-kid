"use client"
import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, FileText, Shield, Users, AlertTriangle, Scale, Mail } from 'lucide-react';

const TermsOfService = () => {
  const [expandedSections, setExpandedSections] = useState({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const sections = [
    {
      id: 'acceptance',
      title: 'Acceptance of Terms',
      icon: <FileText className="w-5 h-5" />,
      content: `Welcome to SearchKid ("the Website," "we," "us," or "our"). By accessing or using our website and services, you ("User," "you," or "your") agree to be bound by these Terms of Service ("Terms," "Agreement"). If you do not agree to all of these terms, you are prohibited from using our website and services.`
    },
    {
      id: 'description',
      title: 'Description of Service',
      icon: <Shield className="w-5 h-5" />,
      content: `Our Website operates as a search engine that indexes and provides links to publicly available channels on the Telegram messaging platform. The service allows users to search for channels based on their queries. We do not host, store, or control the content within the Telegram channels we index. We merely provide a discovery tool.`
    },
    {
      id: 'responsibilities',
      title: 'User Responsibilities and Acceptable Use',
      icon: <Users className="w-5 h-5" />,
      content: `You agree to use our service only for lawful purposes and in accordance with these Terms. You agree not to use our service:

• To violate any applicable law or regulation
• To transmit, or procure the sending of, any advertising or promotional material without our prior written consent
• To impersonate or attempt to impersonate the company, an employee, another user, or any other person or entity
• To engage in any other conduct that restricts or inhibits anyone's use or enjoyment of the Website`
    },
    {
      id: 'content-disclaimer',
      title: 'Content Disclaimer and Third-Party Links',
      icon: <AlertTriangle className="w-5 h-5" />,
      content: `General Disclaimer: Our Website provides links to third-party Telegram channels. We have no control over, and assume no responsibility for, the content, privacy policies, or practices of any third-party channels.

Adult Content Warning: The Telegram channels indexed by our search engine may contain uncensored, sexually explicit, or other adult material. You must be at least 18 years of age to access such content.

No Responsibility: We do not filter or review the content of the channels we index. You access linked channels at your own risk.`
    },
    {
      id: 'intellectual-property',
      title: 'Intellectual Property',
      icon: <Scale className="w-5 h-5" />,
      content: `The Website and its original content, features, and functionality are and will remain the exclusive property of SearchKid and its licensors. Our trademarks may not be used in connection with any product or service without our prior written consent. The content of the indexed Telegram channels belongs to their respective owners.`
    },
    {
      id: 'copyright',
      title: 'Copyright and DMCA Policy',
      icon: <FileText className="w-5 h-5" />,
      content: `We respect the intellectual property rights of others. If you believe that any content linked to by our Website infringes your copyright, please notify us in accordance with our Digital Millennium Copyright Act ("DMCA") Policy by sending a notice of infringement to our designated agent at: darkken415@gmail.com.`
    },
    {
      id: 'limitation',
      title: 'Limitation of Liability',
      icon: <Shield className="w-5 h-5" />,
      content: `To the fullest extent permitted by law, in no event will SearchKid, its affiliates, or their licensors, service providers, employees, agents, officers, or directors be liable for damages of any kind, under any legal theory, arising out of or in connection with your use, or inability to use, the Website.`
    },
    {
      id: 'indemnification',
      title: 'Indemnification',
      icon: <Users className="w-5 h-5" />,
      content: `You agree to defend, indemnify, and hold harmless SearchKid, its affiliates, licensors, and service providers, and its and their respective officers, directors, employees, contractors, agents, licensors, suppliers, successors, and assigns from and against any claims, liabilities, damages, judgments, awards, losses, costs, expenses, or fees arising out of or relating to your violation of these Terms.`
    },
    {
      id: 'termination',
      title: 'Termination',
      icon: <AlertTriangle className="w-5 h-5" />,
      content: `We may terminate or suspend your access to our service immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms. All provisions of the Terms which by their nature should survive termination shall survive termination.`
    },
    {
      id: 'changes',
      title: 'Changes to Terms',
      icon: <FileText className="w-5 h-5" />,
      content: `We reserve the right, at our sole discretion, to modify or replace these Terms at any time. We will provide notice of changes by updating the "Last Updated" date. By continuing to access or use our service after those revisions become effective, you agree to be bound by the revised terms.`
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white font-montserrat">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-pulse animation-delay-4000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 sm:py-12 max-w-4xl">
        {/* Header */}
        <div className={`text-center mb-12 transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-6 animate-bounce">
            <Scale className="w-10 h-10" />
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-lora font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Terms of Service
          </h1>
          <p className="text-lg sm:text-xl text-gray-300 mb-2">Last Updated: {new Intl.DateTimeFormat('en-US').format(new Date())}</p>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-purple-500 mx-auto rounded-full"></div>
        </div>

        {/* Sections */}
        <div className="space-y-6">
          {sections.map((section, index) => (
            <div
              key={section.id}
              className={`backdrop-blur-lg bg-white/10 border border-white/20 rounded-2xl shadow-2xl transform transition-all duration-700 hover:scale-[1.02] hover:bg-white/15 ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
                }`}
              style={{ transitionDelay: `${index * 100}ms` }}
            >
              <button
                onClick={() => toggleSection(section.id)}
                className="w-full p-6 sm:p-8 flex items-center justify-between text-left group transition-all duration-300"
              >
                <div className="flex items-center space-x-4 flex-1">
                  <div className="flex-shrink-0 p-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl group-hover:from-blue-500/30 group-hover:to-purple-500/30 transition-all duration-300">
                    {section.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h2 className="text-xl sm:text-2xl font-lora font-bold text-white group-hover:text-blue-300 transition-colors duration-300">
                      {index + 1}. {section.title}
                    </h2>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-4">
                  {expandedSections[section.id] ? (
                    <ChevronUp className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-all duration-300 transform group-hover:scale-110" />
                  ) : (
                    <ChevronDown className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-all duration-300 transform group-hover:scale-110" />
                  )}
                </div>
              </button>

              <div className={`overflow-hidden transition-all duration-500 ease-in-out ${expandedSections[section.id] ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                }`}>
                <div className="px-6 sm:px-8 pb-6 sm:pb-8 pt-0">
                  <div className="pl-16 sm:pl-20">
                    <div className="w-full h-px bg-gradient-to-r from-blue-500/50 to-purple-500/50 mb-6"></div>
                    <div className="prose prose-invert max-w-none">
                      <p className="text-gray-300 leading-relaxed whitespace-pre-line text-sm sm:text-base">
                        {section.content}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Contact Section */}
        <div className={`mt-12 backdrop-blur-lg bg-white/10 border border-white/20 rounded-2xl p-6 sm:p-8 text-center transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
          }`}>
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-full mb-4">
            <Mail className="w-8 h-8 text-green-400" />
          </div>
          <h3 className="text-2xl font-lora font-bold mb-4 text-white">Contact Us</h3>
          <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
            If you have any questions about these Terms, please don't hesitate to contact us. We're here to help and ensure you have the best experience with our service.
          </p>
          <div className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 hover:shadow-lg">
            <Mail className="w-4 h-4 mr-2" />
            darkken415@gmail.com
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-6"></div>
          <p className="text-gray-400 text-sm">
            © 2025 SearchKid. All rights reserved.
          </p>
        </div>
      </div>

      <style jsx>{`
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default TermsOfService;