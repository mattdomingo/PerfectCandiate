import CodeBlock from '@/components/CodeBlock'
import { 
  CogIcon, 
  DatabaseIcon, 
  CloudIcon,
  DocumentTextIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

export default function SetupPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Setup Guide
          </h1>
          <p className="text-lg text-gray-600">
            Get Perfect Candidate running on your local machine
          </p>
        </div>

        <div className="space-y-8">
          {/* Prerequisites */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <CogIcon className="w-5 h-5 mr-2" />
              Prerequisites
            </h2>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-center">
                <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2" />
                Docker and Docker Compose installed
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2" />
                Node.js 18+ (for local development)
              </li>
              <li className="flex items-center">
                <CheckCircleIcon className="w-4 h-4 text-green-500 mr-2" />
                Python 3.11+ (for local development)
              </li>
            </ul>
          </div>

          {/* Quick Start */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <DocumentTextIcon className="w-5 h-5 mr-2" />
              Quick Start with Docker
            </h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">1. Clone and start services:</h3>
                <CodeBlock language="bash" title="Terminal">
{`git clone <repository-url>
cd perfectCandidate
docker-compose up -d`}
                </CodeBlock>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">2. Access the application:</h3>
                <ul className="space-y-1 text-sm text-gray-600 ml-4">
                  <li>• Frontend: <a href="http://localhost:3000" className="text-primary-600 hover:underline">http://localhost:3000</a></li>
                  <li>• API docs: <a href="http://localhost:8000/docs" className="text-primary-600 hover:underline">http://localhost:8000/docs</a></li>
                  <li>• MinIO console: <a href="http://localhost:9001" className="text-primary-600 hover:underline">http://localhost:9001</a></li>
                </ul>
              </div>
            </div>
          </div>

          {/* Environment Variables */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <CogIcon className="w-5 h-5 mr-2" />
              Environment Configuration
            </h2>
            
            <div className="space-y-6">
              <div>
                <h3 className="font-medium mb-3">API Environment (api/.env)</h3>
                <CodeBlock language="bash" title="api/.env">
{`DATABASE_URL=postgresql://user:password@localhost:5432/perfectcandidate
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=resumes
MINIO_SECURE=false
DEBUG=true
LOG_LEVEL=INFO`}
                </CodeBlock>
              </div>

              <div>
                <h3 className="font-medium mb-3">Frontend Environment (frontend/.env.local)</h3>
                <CodeBlock language="bash" title="frontend/.env.local">
{`NEXT_PUBLIC_API_URL=http://localhost:8000`}
                </CodeBlock>
              </div>
            </div>
          </div>

          {/* MinIO Setup */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <CloudIcon className="w-5 h-5 mr-2" />
              MinIO Storage Setup
            </h2>
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Default Credentials</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li><strong>Access Key:</strong> minioadmin</li>
                  <li><strong>Secret Key:</strong> minioadmin</li>
                  <li><strong>Console URL:</strong> http://localhost:9001</li>
                  <li><strong>API Endpoint:</strong> http://localhost:9000</li>
                </ul>
              </div>
              
              <div>
                <p className="text-gray-700 mb-2">
                  The application automatically creates the required bucket on startup. 
                  You can access the MinIO console to manage files and view uploaded resumes.
                </p>
              </div>
            </div>
          </div>

          {/* Database Setup */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <DatabaseIcon className="w-5 h-5 mr-2" />
              Database Setup
            </h2>
            <div className="space-y-4">
              <p className="text-gray-700">
                PostgreSQL is automatically configured via Docker Compose. 
                Database tables are created automatically when the API starts.
              </p>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium mb-2">Default Database Credentials</h3>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li><strong>Host:</strong> localhost:5432</li>
                  <li><strong>Database:</strong> perfectcandidate</li>
                  <li><strong>Username:</strong> user</li>
                  <li><strong>Password:</strong> password</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Local Development */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Local Development</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-3">Backend Development</h3>
                <CodeBlock language="bash">
{`cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000`}
                </CodeBlock>
              </div>

              <div>
                <h3 className="font-medium mb-3">Frontend Development</h3>
                <CodeBlock language="bash">
{`cd frontend
npm install
npm run dev`}
                </CodeBlock>
              </div>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Troubleshooting</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">Common Issues</h3>
                <ul className="space-y-2 text-gray-700">
                  <li><strong>Port conflicts:</strong> Change ports in docker-compose.yml if 3000, 8000, 5432, or 9000/9001 are in use</li>
                  <li><strong>Permission errors:</strong> Ensure Docker has proper permissions and the current user is in the docker group</li>
                  <li><strong>MinIO connection issues:</strong> Check that MINIO_SECURE is set to "false" for local development</li>
                  <li><strong>Database connection errors:</strong> Ensure PostgreSQL container is running and healthy</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Checking Service Health</h3>
                <CodeBlock language="bash">
{`# Check all service status
docker-compose ps

# View service logs
docker-compose logs api
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs minio

# Restart services
docker-compose restart`}
                </CodeBlock>
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="card bg-primary-50 border-primary-200">
            <h2 className="text-xl font-semibold mb-4 text-primary-900">
              🎉 You're All Set!
            </h2>
            <p className="text-primary-800 mb-4">
              Once everything is running, you can start using Perfect Candidate to optimize resumes.
            </p>
            <div className="flex space-x-4">
              <a 
                href="/app" 
                className="btn-primary"
              >
                Start Using the App
              </a>
              <a 
                href="http://localhost:8000/docs" 
                target="_blank"
                className="btn-outline"
              >
                View API Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


