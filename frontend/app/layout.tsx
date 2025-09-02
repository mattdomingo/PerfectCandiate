import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Perfect Candidate - AI-Powered Resume Optimizer',
  description: 'Optimize your resume for specific job postings using AI-powered analysis and suggestions.',
  keywords: 'resume, optimization, AI, job search, career, matching',
  authors: [{ name: 'Perfect Candidate Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <a href="/" className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">PC</span>
                    </div>
                    <span className="text-xl font-bold text-gray-900">Perfect Candidate</span>
                  </a>
                </div>
                
                <div className="flex items-center space-x-4">
                  <a href="/app" className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    Dashboard
                  </a>
                  <a href="/setup" className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    Setup
                  </a>
                  <a href="/about" className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    About
                  </a>
                  <a href="/contact" className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    Contact
                  </a>
                </div>
              </div>
            </div>
          </nav>
          
          <main className="flex-1">
            {children}
          </main>
          
          <footer className="bg-white border-t border-gray-200 mt-auto">
            <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                  <div className="flex items-center space-x-2 mb-4">
                    <div className="w-6 h-6 bg-primary-600 rounded flex items-center justify-center">
                      <span className="text-white font-bold text-xs">PC</span>
                    </div>
                    <span className="font-bold text-gray-900">Perfect Candidate</span>
                  </div>
                  <p className="text-gray-600 text-sm">
                    AI-powered resume optimization to help you land your dream job.
                  </p>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Features</h3>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li>Resume Analysis</li>
                    <li>Job Matching</li>
                    <li>AI Suggestions</li>
                    <li>Export Options</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Support</h3>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li>Documentation</li>
                    <li>FAQ</li>
                    <li>Contact Us</li>
                    <li>Privacy Policy</li>
                  </ul>
                </div>
              </div>
              
              <div className="mt-8 pt-8 border-t border-gray-200">
                <p className="text-center text-sm text-gray-500">
                  © 2024 Perfect Candidate. All rights reserved.
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
