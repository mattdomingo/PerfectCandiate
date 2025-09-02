'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import axios from 'axios'
import { 
  LinkIcon, 
  DocumentTextIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

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

interface JobAnalysisProps {
  resumeData: ResumeData
  onAnalysisComplete: (data: JobData) => void
}

type InputMethod = 'url' | 'text'

interface FormData {
  method: InputMethod
  job_url: string
  job_text: string
  title: string
  company: string
  location?: string
}

export default function JobAnalysis({ resumeData, onAnalysisComplete }: JobAnalysisProps) {
  const [inputMethod, setInputMethod] = useState<InputMethod>('url')
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    defaultValues: {
      method: 'url'
    }
  })

  const jobUrl = watch('job_url')
  const jobText = watch('job_text')

  const onSubmit = async (data: FormData) => {
    setAnalyzing(true)
    setError(null)
    setSuccess(false)

    try {
      const requestData = {
        job_url: inputMethod === 'url' ? data.job_url || null : null,
        job_text: inputMethod === 'text' ? data.job_text || null : null,
        title: data.title,
        company: data.company,
        location: data.location || null
      }

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/jobs/analyze`,
        requestData
      )

      if (response.data) {
        setSuccess(true)
        setTimeout(() => {
          onAnalysisComplete({
            id: response.data.job_id,
            uuid: response.data.job_uuid,
            title: response.data.title,
            company: response.data.company,
            analysis_summary: response.data.analysis_summary
          })
        }, 1000)
      }
    } catch (err: any) {
      console.error('Analysis error:', err)
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('Failed to analyze job posting. Please try again.')
      }
    } finally {
      setAnalyzing(false)
    }
  }

  const resetAnalysis = () => {
    setError(null)
    setSuccess(false)
  }

  if (success) {
    return (
      <div className="card max-w-2xl mx-auto">
        <div className="text-center py-8">
          <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-green-900 mb-2">
            Job Analysis Complete!
          </h3>
          <p className="text-green-700 mb-4">
            The job posting has been analyzed and requirements extracted. Starting AI matching...
          </p>
          <div className="animate-pulse">
            <div className="w-8 h-8 bg-primary-600 rounded-full mx-auto"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card max-w-4xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="section-title">Analyze Job Posting</h2>
        <p className="text-gray-600">
          Add the job description you want to optimize your resume for
        </p>
      </div>

      {/* Resume Info */}
      <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center">
          <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
          <span className="font-medium text-green-900">Resume: {resumeData.filename}</span>
        </div>
        <div className="text-sm text-green-700 mt-1">
          {resumeData.parsed_data.work_experiences_count} experiences, {' '}
          {resumeData.parsed_data.skills_count} skills extracted
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Input Method Selection */}
        <div>
          <label className="form-label">How would you like to add the job posting?</label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setInputMethod('url')}
              className={`
                p-4 border-2 rounded-lg text-left transition-all
                ${inputMethod === 'url' 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 bg-white hover:border-gray-300'}
              `}
            >
              <div className="flex items-center mb-2">
                <LinkIcon className="w-5 h-5 text-primary-600 mr-2" />
                <span className="font-medium">Job URL</span>
              </div>
              <p className="text-sm text-gray-600">
                Paste the link to the job posting and we'll extract the content
              </p>
            </button>

            <button
              type="button"
              onClick={() => setInputMethod('text')}
              className={`
                p-4 border-2 rounded-lg text-left transition-all
                ${inputMethod === 'text' 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 bg-white hover:border-gray-300'}
              `}
            >
              <div className="flex items-center mb-2">
                <DocumentTextIcon className="w-5 h-5 text-primary-600 mr-2" />
                <span className="font-medium">Manual Text</span>
              </div>
              <p className="text-sm text-gray-600">
                Copy and paste the job description directly
              </p>
            </button>
          </div>
        </div>

        {/* Job Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="form-label">Job Title *</label>
            <input
              type="text"
              {...register('title', { required: 'Job title is required' })}
              className="form-input"
              placeholder="e.g. Senior Software Engineer"
              disabled={analyzing}
            />
            {errors.title && (
              <p className="text-red-600 text-sm mt-1">{errors.title.message}</p>
            )}
          </div>

          <div>
            <label className="form-label">Company *</label>
            <input
              type="text"
              {...register('company', { required: 'Company name is required' })}
              className="form-input"
              placeholder="e.g. Google"
              disabled={analyzing}
            />
            {errors.company && (
              <p className="text-red-600 text-sm mt-1">{errors.company.message}</p>
            )}
          </div>
        </div>

        <div>
          <label className="form-label">Location (optional)</label>
          <input
            type="text"
            {...register('location')}
            className="form-input"
            placeholder="e.g. San Francisco, CA or Remote"
            disabled={analyzing}
          />
        </div>

        {/* Job Content Input */}
        {inputMethod === 'url' ? (
          <div>
            <label className="form-label">Job Posting URL *</label>
            <input
              type="url"
              {...register('job_url', { 
                required: inputMethod === 'url' ? 'Job URL is required' : false 
              })}
              className="form-input"
              placeholder="https://company.com/careers/job-posting"
              disabled={analyzing}
            />
            {errors.job_url && (
              <p className="text-red-600 text-sm mt-1">{errors.job_url.message}</p>
            )}
            <p className="text-sm text-gray-600 mt-2">
              We'll automatically extract the job description from the URL
            </p>
          </div>
        ) : (
          <div>
            <label className="form-label">Job Description *</label>
            <textarea
              {...register('job_text', { 
                required: inputMethod === 'text' ? 'Job description is required' : false,
                minLength: {
                  value: 100,
                  message: 'Job description should be at least 100 characters'
                }
              })}
              className="form-input"
              rows={12}
              placeholder="Paste the complete job description here including requirements, responsibilities, and qualifications..."
              disabled={analyzing}
            />
            {errors.job_text && (
              <p className="text-red-600 text-sm mt-1">{errors.job_text.message}</p>
            )}
            <div className="flex justify-between text-sm text-gray-600 mt-2">
              <span>Minimum 100 characters recommended</span>
              <span>{jobText?.length || 0} characters</span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
            <button
              type="button"
              onClick={resetAnalysis}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Try again
            </button>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-between items-center pt-4">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="btn-outline"
            disabled={analyzing}
          >
            Start Over
          </button>

          <button
            type="submit"
            disabled={analyzing || (!jobUrl && !jobText)}
            className="btn-primary flex items-center space-x-2"
          >
            {analyzing ? (
              <>
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Analyze Job</span>
                <DocumentTextIcon className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Info Box */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">What we analyze:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Required skills and qualifications</li>
          <li>• Preferred experience and education</li>
          <li>• Key responsibilities and duties</li>
          <li>• Important keywords for ATS optimization</li>
        </ul>
      </div>
    </div>
  )
}
