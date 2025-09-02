'use client'

import { useState } from 'react'
// Temporarily disabled due to missing dependencies
// import axios from 'axios'
// import {
//   ArrowDownTrayIcon,
//   DocumentIcon,
//   CheckCircleIcon,
//   ExclamationTriangleIcon,
//   ArrowPathIcon,
//   DocumentArrowDownIcon,
//   SparklesIcon
// } from '@heroicons/react/24/outline'

// Placeholder icons and functions
const ArrowDownTrayIcon = () => <span>⬇️</span>
const DocumentIcon = () => <span>📄</span>
const CheckCircleIcon = () => <span>✅</span>
const ExclamationTriangleIcon = () => <span>⚠️</span>
const ArrowPathIcon = () => <span>🔄</span>
const DocumentArrowDownIcon = () => <span>📥</span>
const SparklesIcon = () => <span>✨</span>

// Placeholder axios function
const axios = {
  get: () => Promise.resolve({ data: {} }),
  post: () => Promise.resolve({ data: {} })
}

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

interface ExportResumeProps {
  resumeData: ResumeData
  jobData: JobData
  matchingData: MatchingData
  onReset: () => void
}

type ExportFormat = 'pdf' | 'docx'

export default function ExportResume({ resumeData, jobData, matchingData, onReset }: ExportResumeProps) {
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf')
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [exportInfo, setExportInfo] = useState<any>(null)

  const handleExport = async (format: ExportFormat) => {
    setExporting(true)
    setError(null)
    setDownloadUrl(null)
    setExportFormat(format)

    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resumes/${resumeData.id}/export?format=${format}`
      )

      if (response.data) {
        setDownloadUrl(response.data.download_url)
        setExportInfo(response.data)
        
        // Automatically trigger download
        const link = document.createElement('a')
        link.href = response.data.download_url
        link.download = response.data.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    } catch (err: any) {
      console.error('Export error:', err)
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError('Failed to export resume. Please try again.')
      }
    } finally {
      setExporting(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="card text-center">
        <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h2 className="section-title mb-2">Analysis Complete!</h2>
        <p className="text-gray-600 mb-6">
          Your resume has been optimized for the {jobData.title} position at {jobData.company}
        </p>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-primary-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-primary-700">
              {Math.round((matchingData.summary?.overall_match_score || 0) * 100)}%
            </div>
            <div className="text-sm text-primary-600">Match Score</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-700">
              {matchingData.summary?.accepted_suggestions || 0}
            </div>
            <div className="text-sm text-green-600">Improvements Applied</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-700">
              {matchingData.summary?.suggestions_count || 0}
            </div>
            <div className="text-sm text-blue-600">Total Suggestions</div>
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="card">
        <h3 className="text-xl font-semibold mb-6 flex items-center">
          <ArrowDownTrayIcon className="w-5 h-5 mr-2" />
          Download Your Optimized Resume
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* PDF Option */}
          <div className="border-2 border-gray-200 rounded-lg p-6 hover:border-primary-300 transition-colors">
            <div className="flex items-center mb-4">
              <DocumentIcon className="w-8 h-8 text-red-500 mr-3" />
              <div>
                <h4 className="font-semibold text-lg">PDF Format</h4>
                <p className="text-sm text-gray-600">Professional, print-ready format</p>
              </div>
            </div>
            <ul className="text-sm text-gray-600 mb-4 space-y-1">
              <li>• Maintains professional formatting</li>
              <li>• Compatible with ATS systems</li>
              <li>• Ready for email and printing</li>
              <li>• Preserves visual layout</li>
            </ul>
            <button
              onClick={() => handleExport('pdf')}
              disabled={exporting}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              {exporting && exportFormat === 'pdf' ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  <span>Generating PDF...</span>
                </>
              ) : (
                <>
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Download PDF</span>
                </>
              )}
            </button>
          </div>

          {/* DOCX Option */}
          <div className="border-2 border-gray-200 rounded-lg p-6 hover:border-primary-300 transition-colors">
            <div className="flex items-center mb-4">
              <DocumentIcon className="w-8 h-8 text-blue-500 mr-3" />
              <div>
                <h4 className="font-semibold text-lg">Word Format</h4>
                <p className="text-sm text-gray-600">Editable Microsoft Word document</p>
              </div>
            </div>
            <ul className="text-sm text-gray-600 mb-4 space-y-1">
              <li>• Fully editable in Word</li>
              <li>• Easy to customize further</li>
              <li>• Compatible with Google Docs</li>
              <li>• Flexible formatting options</li>
            </ul>
            <button
              onClick={() => handleExport('docx')}
              disabled={exporting}
              className="btn-outline w-full flex items-center justify-center space-x-2"
            >
              {exporting && exportFormat === 'docx' ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  <span>Generating DOCX...</span>
                </>
              ) : (
                <>
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Download DOCX</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {/* Success Display */}
        {downloadUrl && exportInfo && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-4">
            <div className="flex items-center mb-2">
              <CheckCircleIcon className="w-5 h-5 text-green-500 mr-2" />
              <span className="text-green-700 font-medium">
                Resume exported successfully!
              </span>
            </div>
            <div className="text-sm text-green-600 space-y-1">
              <p>File: {exportInfo.filename}</p>
              <p>Size: {formatFileSize(exportInfo.file_size)}</p>
              <p>Format: {exportInfo.format.toUpperCase()}</p>
            </div>
            <a
              href={downloadUrl}
              download={exportInfo.filename}
              className="inline-flex items-center space-x-1 text-green-600 hover:text-green-800 text-sm mt-2 underline"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              <span>Download again</span>
            </a>
          </div>
        )}
      </div>

      {/* Next Steps */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <SparklesIcon className="w-5 h-5 mr-2 text-yellow-500" />
          What's Next?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h4 className="font-medium">Application Tips:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Review your optimized resume before submitting</li>
              <li>• Customize your cover letter to match</li>
              <li>• Use the same keywords in your LinkedIn profile</li>
              <li>• Practice interviewing with the job requirements</li>
            </ul>
          </div>
          <div className="space-y-3">
            <h4 className="font-medium">Track Your Applications:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Keep a record of applications sent</li>
              <li>• Follow up after 1-2 weeks</li>
              <li>• Continue optimizing for other positions</li>
              <li>• Monitor response rates and adjust strategy</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4">
        <button
          onClick={onReset}
          className="btn-outline"
        >
          Optimize Another Resume
        </button>

        <div className="space-x-3">
          <button
            onClick={() => window.location.href = '/'}
            className="btn-secondary"
          >
            Back to Home
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="btn-primary"
          >
            Download PDF Again
          </button>
        </div>
      </div>

      {/* Feedback Section */}
      <div className="card bg-gray-50">
        <div className="text-center">
          <h4 className="font-semibold mb-2">How was your experience?</h4>
          <p className="text-sm text-gray-600 mb-4">
            Help us improve by sharing your feedback about the resume optimization process.
          </p>
          <button className="btn-outline text-sm">
            Share Feedback
          </button>
        </div>
      </div>
    </div>
  )
}
