'use client'

import { useState } from 'react'

// Temporarily disabled all component imports due to missing dependencies
// import ResumeUpload from '@/components/ResumeUpload'
// import JobAnalysis from '@/components/JobAnalysis'
// import MatchingResults from '@/components/MatchingResults'
// import ExportResume from '@/components/ExportResume'

// Placeholder icons
const DocumentArrowUpIcon = () => <span>📄</span>
const BriefcaseIcon = () => <span>💼</span>
const ChartBarIcon = () => <span>📊</span>
const ArrowDownTrayIcon = () => <span>⬇️</span>

type Step = 'upload' | 'job' | 'analysis' | 'export'

interface ResumeData {
  id: number
  uuid: string
  filename: string
  parsed_data: any
}

interface JobData {
  id: number
  uuid: string
  title: string
  company: string
  analysis_summary: any
}

interface MatchingData {
  matching_result_id: number
  matching_result_uuid: string
  summary: any
}

export default function AppPage() {
  const [currentStep, setCurrentStep] = useState<Step>('upload')
  const [resumeData, setResumeData] = useState<ResumeData | null>(null)
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [matchingData, setMatchingData] = useState<MatchingData | null>(null)

  const steps = [
    { id: 'upload', name: 'Upload Resume', icon: DocumentArrowUpIcon },
    { id: 'job', name: 'Job Analysis', icon: BriefcaseIcon },
    { id: 'analysis', name: 'AI Analysis', icon: ChartBarIcon },
    { id: 'export', name: 'Export Resume', icon: ArrowDownTrayIcon },
  ]

  const getStepStatus = (stepId: Step) => {
    const stepIndex = steps.findIndex(s => s.id === stepId)
    const currentIndex = steps.findIndex(s => s.id === currentStep)
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  const handleResumeUpload = (data: ResumeData) => {
    setResumeData(data)
    setCurrentStep('job')
  }

  const handleJobAnalysis = (data: JobData) => {
    setJobData(data)
    setCurrentStep('analysis')
  }

  const handleMatchingComplete = (data: MatchingData) => {
    setMatchingData(data)
    setCurrentStep('export')
  }

  const handleReset = () => {
    setCurrentStep('upload')
    setResumeData(null)
    setJobData(null)
    setMatchingData(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Resume Optimizer
          </h1>
          <p className="text-lg text-gray-600">
            Upload your resume, analyze job requirements, and get AI-powered optimization suggestions
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-center">
            <div className="flex items-center space-x-8">
              {steps.map((step, index) => {
                const Icon = step.icon
                const status = getStepStatus(step.id as Step)
                
                return (
                  <div key={step.id} className="flex items-center">
                    <div className="flex flex-col items-center">
                      <div className={`
                        step-indicator 
                        ${status === 'active' ? 'step-active' : 
                          status === 'completed' ? 'step-completed' : 'step-pending'}
                      `}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className={`
                        mt-2 text-sm font-medium
                        ${status === 'active' ? 'text-primary-600' :
                          status === 'completed' ? 'text-green-600' : 'text-gray-500'}
                      `}>
                        {step.name}
                      </span>
                    </div>
                    
                    {index < steps.length - 1 && (
                      <div className={`
                        w-16 h-0.5 mx-4 mt-[-20px]
                        ${index < steps.findIndex(s => s.id === currentStep) ? 
                          'bg-green-600' : 'bg-gray-300'}
                      `} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-4">Resume Rewriter App</h2>
              <p className="text-gray-600 mb-4">
                Upload your resume, enter a job description, and get AI-powered suggestions to optimize your resume.
              </p>

              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-md">
                  <h3 className="font-medium text-blue-900">Step 1: Upload Resume</h3>
                  <p className="text-blue-700">Upload your current resume (PDF format)</p>
                </div>

                <div className="p-4 bg-green-50 rounded-md">
                  <h3 className="font-medium text-green-900">Step 2: Job Description</h3>
                  <p className="text-green-700">Paste job description URL or text</p>
                </div>

                <div className="p-4 bg-purple-50 rounded-md">
                  <h3 className="font-medium text-purple-900">Step 3: AI Analysis</h3>
                  <p className="text-purple-700">Get personalized suggestions and inline edits</p>
                </div>

                <div className="p-4 bg-orange-50 rounded-md">
                  <h3 className="font-medium text-orange-900">Step 4: Download</h3>
                  <p className="text-orange-700">Export your optimized resume (PDF/DOCX)</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Debug Info (remove in production) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-12 max-w-4xl mx-auto">
            <details className="bg-gray-100 p-4 rounded-lg">
              <summary className="font-semibold cursor-pointer">Debug Info</summary>
              <pre className="mt-2 text-xs overflow-auto">
                {JSON.stringify({ 
                  currentStep, 
                  resumeData: resumeData ? { id: resumeData.id, filename: resumeData.filename } : null,
                  jobData: jobData ? { id: jobData.id, title: jobData.title, company: jobData.company } : null,
                  matchingData: matchingData ? { id: matchingData.matching_result_id } : null
                }, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  )
}
