'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  ChartBarIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  ArrowPathIcon,
  LightBulbIcon,
  XMarkIcon,
  StarIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'

import ResumeDiffEditor from './ResumeDiffEditor'

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

interface Suggestion {
  id: number
  uuid: string
  suggestion_type: string
  section: string
  priority: number
  original_content: string | null
  suggested_content: string
  reasoning: string
  estimated_impact: number
  confidence_score: number
  is_accepted: boolean | null
}

interface MatchingResult {
  id: number
  overall_match_score: number
  skills_match_score: number
  experience_match_score: number
  education_match_score: number
  matching_skills: any[]
  missing_skills: any[]
  gaps_analysis: any
  strengths_analysis: any
  requirements_coverage: any
  keyword_matches: any
}

interface MatchingResultsProps {
  resumeData: ResumeData
  jobData: JobData
  onMatchingComplete: (data: MatchingData) => void
}

export default function MatchingResults({ resumeData, jobData, onMatchingComplete }: MatchingResultsProps) {
  const [matching, setMatching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [matchingResult, setMatchingResult] = useState<MatchingResult | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [selectedSuggestion, setSelectedSuggestion] = useState<Suggestion | null>(null)
  const [processingMatchingId, setProcessingMatchingId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'editor'>('overview')
  const [editedContent, setEditedContent] = useState<string>('')
  const [originalResumeText, setOriginalResumeText] = useState<string>('')

  useEffect(() => {
    performMatching()
    fetchResumeText()
  }, [])

  const fetchResumeText = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/resumes/${resumeData.id}/text`
      )
      setOriginalResumeText(response.data.formatted_text)
    } catch (err) {
      console.error('Error fetching resume text:', err)
      // Fallback to empty text if fetch fails
      setOriginalResumeText('')
    }
  }

  const performMatching = async () => {
    setMatching(true)
    setError(null)

    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/match/compare`,
        {
          resume_id: resumeData.id,
          job_id: jobData.id
        }
      )

      if (response.data && response.data.matching_result_id) {
        setProcessingMatchingId(response.data.matching_result_id)
        
        // Fetch detailed matching results
        await fetchMatchingResults(response.data.matching_result_id)
        
        // Fetch suggestions
        await fetchSuggestions(response.data.matching_result_id)
      }
    } catch (err: any) {
      console.error('Matching error:', err)
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError('Failed to perform matching analysis. Please try again.')
      }
    } finally {
      setMatching(false)
    }
  }

  const fetchMatchingResults = async (matchingId: number) => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/match/results/${matchingId}`
      )
      setMatchingResult(response.data)
    } catch (err) {
      console.error('Error fetching matching results:', err)
    }
  }

  const fetchSuggestions = async (matchingId: number) => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/match/results/${matchingId}/suggestions`
      )
      setSuggestions(response.data)
    } catch (err) {
      console.error('Error fetching suggestions:', err)
    }
  }

  const handleSuggestionAction = async (suggestionId: number, isAccepted: boolean) => {
    try {
      await axios.put(
        `${process.env.NEXT_PUBLIC_API_URL}/api/match/suggestions/${suggestionId}`,
        {
          is_accepted: isAccepted,
          user_notes: null
        }
      )

      // Update local state
      setSuggestions(prev => 
        prev.map(s => 
          s.id === suggestionId 
            ? { ...s, is_accepted: isAccepted }
            : s
        )
      )
    } catch (err) {
      console.error('Error updating suggestion:', err)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBackground = (score: number) => {
    if (score >= 0.8) return 'bg-green-100'
    if (score >= 0.6) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  const handleContentChange = (newContent: string) => {
    setEditedContent(newContent)
  }

  const handleSuggestionUpdate = async (suggestionId: number, isAccepted: boolean) => {
    // Update suggestion status via API
    await handleSuggestionAction(suggestionId, isAccepted)
  }

  const getOriginalResumeText = () => {
    return originalResumeText
  }

  const handleContinue = () => {
    if (processingMatchingId) {
      onMatchingComplete({
        matching_result_id: processingMatchingId,
        matching_result_uuid: matchingResult?.id.toString() || '',
        summary: {
          overall_match_score: matchingResult?.overall_match_score,
          suggestions_count: suggestions.length,
          accepted_suggestions: suggestions.filter(s => s.is_accepted === true).length
        }
      })
    }
  }

  if (matching) {
    return (
      <div className="card max-w-2xl mx-auto">
        <div className="text-center py-8">
          <ArrowPathIcon className="w-16 h-16 text-primary-500 mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Analyzing Resume Match
          </h3>
          <p className="text-gray-600 mb-4">
            Our AI is comparing your resume with the job requirements...
          </p>
          <div className="text-sm text-gray-500">
            This may take a few moments as we perform semantic analysis
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card max-w-2xl mx-auto">
        <div className="text-center py-8">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-red-900 mb-2">
            Analysis Failed
          </h3>
          <p className="text-red-700 mb-4">{error}</p>
          <button
            onClick={performMatching}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0">AI Matching Analysis</h2>
          <div className="text-sm text-gray-600">
            {resumeData.filename} vs {jobData.title} at {jobData.company}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'overview'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <ChartBarIcon className="w-4 h-4 inline mr-2" />
            Analysis Overview
          </button>
          <button
            onClick={() => setActiveTab('editor')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'editor'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <CodeBracketIcon className="w-4 h-4 inline mr-2" />
            Resume Editor
          </button>
        </div>

        {/* Overall Score - Only show in overview tab */}
        {activeTab === 'overview' && matchingResult && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded-lg ${getScoreBackground(matchingResult.overall_match_score)}`}>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(matchingResult.overall_match_score * 100)}%
              </div>
              <div className="text-sm text-gray-600">Overall Match</div>
            </div>
            <div className={`p-4 rounded-lg ${getScoreBackground(matchingResult.skills_match_score)}`}>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(matchingResult.skills_match_score * 100)}%
              </div>
              <div className="text-sm text-gray-600">Skills Match</div>
            </div>
            <div className={`p-4 rounded-lg ${getScoreBackground(matchingResult.experience_match_score)}`}>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(matchingResult.experience_match_score * 100)}%
              </div>
              <div className="text-sm text-gray-600">Experience Match</div>
            </div>
            <div className={`p-4 rounded-lg ${getScoreBackground(matchingResult.education_match_score)}`}>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(matchingResult.education_match_score * 100)}%
              </div>
              <div className="text-sm text-gray-600">Education Match</div>
            </div>
          </div>
        )}
      </div>

      {/* Editor Tab Content */}
      {activeTab === 'editor' && (
        <ResumeDiffEditor
          originalContent={getOriginalResumeText()}
          suggestions={suggestions}
          onContentChange={handleContentChange}
          onSuggestionUpdate={handleSuggestionUpdate}
        />
      )}

      {/* Overview Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Existing content wrapped in fragment */}

      {/* Suggestions */}
      <div className="card">
        <h3 className="text-xl font-semibold mb-4 flex items-center">
          <LightBulbIcon className="w-5 h-5 mr-2 text-yellow-500" />
          AI Suggestions ({suggestions.length})
        </h3>

        {suggestions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No suggestions available at this time.
          </div>
        ) : (
          <div className="space-y-4">
            {suggestions
              .sort((a, b) => b.priority - a.priority)
              .map((suggestion) => (
                <div 
                  key={suggestion.id}
                  className={`
                    p-4 border rounded-lg transition-all
                    ${suggestion.is_accepted === true ? 'border-green-500 bg-green-50' :
                      suggestion.is_accepted === false ? 'border-red-500 bg-red-50' :
                      'border-gray-200 bg-white hover:border-primary-300'}
                  `}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className={`
                          px-2 py-1 text-xs font-medium rounded-full mr-2
                          ${suggestion.priority >= 4 ? 'bg-red-100 text-red-800' :
                            suggestion.priority >= 3 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'}
                        `}>
                          Priority {suggestion.priority}
                        </span>
                        <span className="text-sm text-gray-600 capitalize">
                          {suggestion.section} • {suggestion.suggestion_type}
                        </span>
                        <div className="flex items-center ml-2">
                          {[...Array(Math.round(suggestion.confidence_score * 5))].map((_, i) => (
                            <StarIcon key={i} className="w-3 h-3 text-yellow-400 fill-current" />
                          ))}
                        </div>
                      </div>
                      
                      <h4 className="font-medium text-gray-900 mb-2">
                        {suggestion.suggested_content}
                      </h4>
                      
                      <p className="text-sm text-gray-600 mb-3">
                        {suggestion.reasoning}
                      </p>

                      {suggestion.estimated_impact && (
                        <div className="text-xs text-gray-500">
                          Estimated impact: +{Math.round(suggestion.estimated_impact * 100)}% match score
                        </div>
                      )}
                    </div>

                    {suggestion.is_accepted === null && (
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => handleSuggestionAction(suggestion.id, true)}
                          className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded hover:bg-green-200 transition-colors"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => handleSuggestionAction(suggestion.id, false)}
                          className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded hover:bg-red-200 transition-colors"
                        >
                          Reject
                        </button>
                      </div>
                    )}

                    {suggestion.is_accepted === true && (
                      <div className="flex items-center text-green-600 ml-4">
                        <CheckCircleIcon className="w-5 h-5" />
                        <span className="text-sm ml-1">Accepted</span>
                      </div>
                    )}

                    {suggestion.is_accepted === false && (
                      <div className="flex items-center text-red-600 ml-4">
                        <XMarkIcon className="w-5 h-5" />
                        <span className="text-sm ml-1">Rejected</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Detailed Analysis */}
      {matchingResult && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-green-700">
              Your Strengths
            </h3>
            {matchingResult.strengths_analysis?.strong_skill_matches?.length > 0 ? (
              <ul className="space-y-2">
                {matchingResult.strengths_analysis.strong_skill_matches.map((strength: any, index: number) => (
                  <li key={index} className="flex items-center text-sm">
                    <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                    <span>{strength.skill}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 text-sm">No specific strengths identified</p>
            )}
          </div>

          {/* Gaps */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-red-700">
              Areas for Improvement
            </h3>
            {matchingResult.missing_skills?.length > 0 ? (
              <ul className="space-y-2">
                {matchingResult.missing_skills.slice(0, 5).map((skill: any, index: number) => (
                  <li key={index} className="flex items-center text-sm">
                    <ExclamationTriangleIcon className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" />
                    <span>{skill.skill}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 text-sm">No significant gaps identified</p>
            )}
          </div>
        </div>
      )}

        </>
      )}

      {/* Continue Button - Show for both tabs */}
      <div className="flex justify-between items-center pt-4">
        <button
          onClick={() => window.location.reload()}
          className="btn-outline"
        >
          Start Over
        </button>

        <button
          onClick={handleContinue}
          className="btn-primary"
          disabled={!matchingResult}
        >
          Continue to Export
        </button>
      </div>
    </div>
  )
}
