import Link from 'next/link'
import { 
  DocumentTextIcon, 
  BriefcaseIcon, 
  SparklesIcon, 
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-purple-800 text-white">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Perfect Your Resume with{' '}
              <span className="text-gradient bg-gradient-to-r from-yellow-400 to-orange-500">
                AI-Powered
              </span>{' '}
              Analysis
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto">
              Upload your resume, paste a job description, and get intelligent suggestions 
              to optimize your application for any position.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/app" 
                className="btn-primary text-lg px-8 py-3 rounded-lg inline-flex items-center space-x-2"
              >
                <SparklesIcon className="w-5 h-5" />
                <span>Start Optimizing</span>
              </Link>
              <button className="btn-outline bg-white/10 border-white/30 text-white hover:bg-white/20 text-lg px-8 py-3 rounded-lg">
                Watch Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered platform analyzes your resume against job requirements 
              and provides actionable suggestions for improvement.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <DocumentTextIcon className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Upload Resume</h3>
              <p className="text-gray-600">
                Upload your PDF resume and our system will extract and parse your information.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BriefcaseIcon className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Add Job Description</h3>
              <p className="text-gray-600">
                Paste the job posting URL or description you want to optimize for.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ChartBarIcon className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Get AI Analysis</h3>
              <p className="text-gray-600">
                Receive detailed matching scores and intelligent improvement suggestions.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ArrowDownTrayIcon className="w-8 h-8 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Export Optimized Resume</h3>
              <p className="text-gray-600">
                Download your improved resume as PDF or DOCX with applied suggestions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Why Choose Perfect Candidate?
              </h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-lg">AI-Powered Analysis</h3>
                    <p className="text-gray-600">
                      Advanced semantic matching using state-of-the-art NLP models.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-lg">Detailed Insights</h3>
                    <p className="text-gray-600">
                      Get comprehensive matching scores and gap analysis.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-lg">Smart Suggestions</h3>
                    <p className="text-gray-600">
                      Receive actionable recommendations to improve your match score.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-6 h-6 text-green-500 mt-1 flex-shrink-0" />
                  <div>
                    <h3 className="font-semibold text-lg">Multiple Export Formats</h3>
                    <p className="text-gray-600">
                      Download optimized resumes as PDF or DOCX files.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="text-center">
                <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <SparklesIcon className="w-10 h-10 text-primary-600" />
                </div>
                <h3 className="text-2xl font-bold mb-4">Ready to Get Started?</h3>
                <p className="text-gray-600 mb-6">
                  Join thousands of job seekers who have optimized their resumes with our AI platform.
                </p>
                <Link 
                  href="/app" 
                  className="btn-primary text-lg px-8 py-3 rounded-lg w-full inline-flex items-center justify-center space-x-2"
                >
                  <span>Start Your Analysis</span>
                  <SparklesIcon className="w-5 h-5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-white mb-2">10,000+</div>
              <div className="text-blue-100">Resumes Optimized</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">85%</div>
              <div className="text-blue-100">Average Match Improvement</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-white mb-2">4.9/5</div>
              <div className="text-blue-100">User Satisfaction</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
