'use client'

import { useState, useEffect, useRef } from 'react'
import { Editor, DiffEditor } from '@monaco-editor/react'
import { 
  CodeBracketIcon, 
  DocumentTextIcon, 
  CheckCircleIcon, 
  XMarkIcon,
  ArrowPathIcon,
  EyeIcon,
  PencilIcon
} from '@heroicons/react/24/outline'

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

interface ResumeDiffEditorProps {
  originalContent: string
  suggestions: Suggestion[]
  onContentChange: (newContent: string) => void
  onSuggestionUpdate: (suggestionId: number, isAccepted: boolean) => void
}

type ViewMode = 'original' | 'suggested' | 'diff' | 'edit'

export default function ResumeDiffEditor({ 
  originalContent, 
  suggestions, 
  onContentChange, 
  onSuggestionUpdate 
}: ResumeDiffEditorProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('diff')
  const [modifiedContent, setModifiedContent] = useState('')
  const [selectedSuggestion, setSelectedSuggestion] = useState<Suggestion | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [currentContent, setCurrentContent] = useState(originalContent)
  const editorRef = useRef<any>(null)

  useEffect(() => {
    // Apply accepted suggestions to create modified content
    let content = originalContent
    
    const acceptedSuggestions = suggestions.filter(s => s.is_accepted === true)
    
    // Apply suggestions in priority order
    acceptedSuggestions
      .sort((a, b) => b.priority - a.priority)
      .forEach(suggestion => {
        if (suggestion.original_content && suggestion.suggested_content) {
          // Replace original content with suggested content
          content = content.replace(
            suggestion.original_content,
            suggestion.suggested_content
          )
        } else if (suggestion.suggestion_type === 'add') {
          // Add new content (append to relevant section)
          content += `\n\n${suggestion.suggested_content}`
        }
      })
    
    setModifiedContent(content)
    setCurrentContent(content)
  }, [originalContent, suggestions])

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
    
    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      lineHeight: 20,
      wordWrap: 'on',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      renderLineHighlight: 'line',
      selectOnLineNumbers: true
    })
  }

  const handleSuggestionClick = (suggestion: Suggestion) => {
    setSelectedSuggestion(suggestion)
    
    if (suggestion.original_content && editorRef.current) {
      // Find and highlight the relevant text in the editor
      const model = editorRef.current.getModel()
      if (model) {
        const text = model.getValue()
        const startPos = text.indexOf(suggestion.original_content)
        if (startPos !== -1) {
          const endPos = startPos + suggestion.original_content.length
          const startPosition = model.getPositionAt(startPos)
          const endPosition = model.getPositionAt(endPos)
          
          // Set selection and scroll to it
          editorRef.current.setSelection({
            startLineNumber: startPosition.lineNumber,
            startColumn: startPosition.column,
            endLineNumber: endPosition.lineNumber,
            endColumn: endPosition.column
          })
          editorRef.current.revealRangeInCenter({
            startLineNumber: startPosition.lineNumber,
            startColumn: startPosition.column,
            endLineNumber: endPosition.lineNumber,
            endColumn: endPosition.column
          })
        }
      }
    }
  }

  const handleAcceptSuggestion = (suggestion: Suggestion) => {
    onSuggestionUpdate(suggestion.id, true)
    setSelectedSuggestion(null)
  }

  const handleRejectSuggestion = (suggestion: Suggestion) => {
    onSuggestionUpdate(suggestion.id, false)
    setSelectedSuggestion(null)
  }

  const handleContentEdit = (value: string | undefined) => {
    if (value !== undefined) {
      setCurrentContent(value)
      onContentChange(value)
    }
  }

  const getEditorTheme = () => {
    return viewMode === 'diff' ? 'vs' : 'vs'
  }

  const pendingSuggestions = suggestions.filter(s => s.is_accepted === null)
  const acceptedSuggestions = suggestions.filter(s => s.is_accepted === true)
  const rejectedSuggestions = suggestions.filter(s => s.is_accepted === false)

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Resume Editor</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {pendingSuggestions.length} pending • {acceptedSuggestions.length} accepted
            </span>
          </div>
        </div>
        
        {/* View Mode Selector */}
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode('original')}
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'original' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <DocumentTextIcon className="w-4 h-4 inline mr-1" />
            Original
          </button>
          <button
            onClick={() => setViewMode('suggested')}
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'suggested' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <CheckCircleIcon className="w-4 h-4 inline mr-1" />
            With Suggestions
          </button>
          <button
            onClick={() => setViewMode('diff')}
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'diff' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <CodeBracketIcon className="w-4 h-4 inline mr-1" />
            Side-by-Side
          </button>
          <button
            onClick={() => {
              setViewMode('edit')
              setIsEditing(true)
            }}
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              viewMode === 'edit' 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <PencilIcon className="w-4 h-4 inline mr-1" />
            Edit
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Main Editor Area */}
        <div className="flex-1">
          {viewMode === 'diff' ? (
            <DiffEditor
              height="600px"
              original={originalContent}
              modified={modifiedContent}
              language="plaintext"
              theme={getEditorTheme()}
              options={{
                readOnly: true,
                fontSize: 14,
                lineHeight: 20,
                wordWrap: 'on',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                renderSideBySide: true,
                ignoreTrimWhitespace: false,
                renderWhitespace: 'none'
              }}
            />
          ) : viewMode === 'edit' ? (
            <Editor
              height="600px"
              defaultLanguage="plaintext"
              value={currentContent}
              onChange={handleContentEdit}
              onMount={handleEditorDidMount}
              theme={getEditorTheme()}
              options={{
                fontSize: 14,
                lineHeight: 20,
                wordWrap: 'on',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                readOnly: false
              }}
            />
          ) : (
            <Editor
              height="600px"
              defaultLanguage="plaintext"
              value={viewMode === 'original' ? originalContent : modifiedContent}
              onMount={handleEditorDidMount}
              theme={getEditorTheme()}
              options={{
                readOnly: true,
                fontSize: 14,
                lineHeight: 20,
                wordWrap: 'on',
                minimap: { enabled: false },
                scrollBeyondLastLine: false
              }}
            />
          )}
        </div>

        {/* Suggestions Panel */}
        <div className="w-80 border-l border-gray-200 bg-gray-50">
          <div className="p-4">
            <h4 className="font-medium text-gray-900 mb-3">
              Suggestions ({pendingSuggestions.length})
            </h4>
            
            {pendingSuggestions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircleIcon className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <p className="text-sm">All suggestions reviewed!</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {pendingSuggestions
                  .sort((a, b) => b.priority - a.priority)
                  .map((suggestion) => (
                    <div
                      key={suggestion.id}
                      className={`
                        p-3 bg-white rounded-lg border cursor-pointer transition-all
                        ${selectedSuggestion?.id === suggestion.id
                          ? 'border-primary-500 ring-2 ring-primary-200'
                          : 'border-gray-200 hover:border-gray-300'}
                      `}
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`
                          px-2 py-1 text-xs font-medium rounded-full
                          ${suggestion.priority >= 4 ? 'bg-red-100 text-red-800' :
                            suggestion.priority >= 3 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'}
                        `}>
                          Priority {suggestion.priority}
                        </span>
                        <span className="text-xs text-gray-500 capitalize">
                          {suggestion.section}
                        </span>
                      </div>
                      
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {suggestion.suggested_content.length > 60
                          ? `${suggestion.suggested_content.substring(0, 60)}...`
                          : suggestion.suggested_content}
                      </p>
                      
                      <p className="text-xs text-gray-600 mb-3">
                        {suggestion.reasoning.length > 80
                          ? `${suggestion.reasoning.substring(0, 80)}...`
                          : suggestion.reasoning}
                      </p>

                      <div className="flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleAcceptSuggestion(suggestion)
                          }}
                          className="flex-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded hover:bg-green-200 transition-colors"
                        >
                          Accept
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRejectSuggestion(suggestion)
                          }}
                          className="flex-1 px-2 py-1 bg-red-100 text-red-800 text-xs rounded hover:bg-red-200 transition-colors"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}

            {/* Summary */}
            {(acceptedSuggestions.length > 0 || rejectedSuggestions.length > 0) && (
              <div className="mt-6 pt-4 border-t border-gray-300">
                <h5 className="font-medium text-gray-700 mb-2">Review Summary</h5>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-600">Accepted:</span>
                    <span>{acceptedSuggestions.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-red-600">Rejected:</span>
                    <span>{rejectedSuggestions.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-yellow-600">Pending:</span>
                    <span>{pendingSuggestions.length}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {viewMode === 'edit' ? (
              <span className="flex items-center">
                <PencilIcon className="w-4 h-4 mr-1" />
                Editing mode - Changes are saved automatically
              </span>
            ) : viewMode === 'diff' ? (
              'Side-by-side comparison showing original vs. suggested changes'
            ) : (
              `Viewing ${viewMode} version of your resume`
            )}
          </div>
          
          <div className="flex space-x-2">
            {isEditing && (
              <button
                onClick={() => {
                  setIsEditing(false)
                  setViewMode('suggested')
                }}
                className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded hover:bg-primary-200 transition-colors"
              >
                Save Changes
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}


