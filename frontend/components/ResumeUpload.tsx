'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { 
  DocumentArrowUpIcon, 
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

interface ResumeUploadProps {
  onUploadComplete: (data: ResumeData) => void
}

export default function ResumeUpload({ onUploadComplete }: ResumeUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file type
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file only.')
      return
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB.')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(false)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resumes/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              setUploadProgress(progress)
            }
          },
        }
      )

      if (response.data) {
        setSuccess(true)
        setTimeout(() => {
          onUploadComplete({
            id: response.data.resume_id,
            uuid: response.data.resume_uuid,
            filename: response.data.filename,
            parsed_data: response.data.parsed_data
          })
        }, 1000)
      }
    } catch (err: any) {
      console.error('Upload error:', err)
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else if (err.message) {
        setError(err.message)
      } else {
        setError('Failed to upload resume. Please try again.')
      }
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: uploading || success
  })

  const resetUpload = () => {
    setError(null)
    setSuccess(false)
    setUploadProgress(0)
  }

  return (
    <div className="card max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="section-title">Upload Your Resume</h2>
        <p className="text-gray-600">
          Upload your PDF resume to get started with AI-powered optimization
        </p>
      </div>

      {!success ? (
        <div>
          <div
            {...getRootProps()}
            className={`
              file-upload-zone cursor-pointer
              ${isDragActive ? 'dragover' : ''}
              ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input {...getInputProps()} />
            
            <div className="text-center">
              {uploading ? (
                <ArrowPathIcon className="w-12 h-12 text-primary-500 mx-auto mb-4 animate-spin" />
              ) : (
                <DocumentArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              )}
              
              <div className="text-lg font-medium text-gray-900 mb-2">
                {uploading ? 'Processing your resume...' :
                 isDragActive ? 'Drop your resume here' :
                 'Drag and drop your resume'}
              </div>
              
              <div className="text-sm text-gray-600 mb-4">
                {uploading ? 'Please wait while we extract and analyze your resume content' :
                 'or click to browse and select a PDF file'}
              </div>

              {!uploading && (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={(e) => e.stopPropagation()}
                >
                  Choose File
                </button>
              )}
            </div>
          </div>

          {uploading && (
            <div className="mt-6">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
              <button
                onClick={resetUpload}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          )}

          <div className="mt-6 text-xs text-gray-500 text-center">
            <p>Supported format: PDF only</p>
            <p>Maximum file size: 10MB</p>
            <p>Your resume data is processed securely and never shared</p>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-green-900 mb-2">
            Resume Uploaded Successfully!
          </h3>
          <p className="text-green-700 mb-4">
            Your resume has been processed and analyzed. Moving to the next step...
          </p>
          <div className="animate-pulse">
            <div className="w-8 h-8 bg-primary-600 rounded-full mx-auto"></div>
          </div>
        </div>
      )}

      {/* Sample Resume Info */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">What happens next?</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Your PDF is processed to extract text content</li>
          <li>• AI parses your experience, skills, and education</li>
          <li>• Structured data is prepared for job matching</li>
          <li>• You'll be able to add a job description for analysis</li>
        </ul>
      </div>
    </div>
  )
}
