import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="container">
      <header className="app-header">
        <div className="brand">
          <div className="logo" aria-hidden />
          <div>
            <div className="title">Perfect Candidate</div>
            <div className="subtitle">Resume Rewriter</div>
          </div>
        </div>
        <nav className="actions">
          <Link href="/login" className="btn">Log in</Link>
          <Link href="/app" className="btn btn-primary">Get started</Link>
        </nav>
      </header>

      <section className="card" style={{marginTop: 16}}>
        <h1 className="title" style={{margin: 0}}>Make your resume the perfect match</h1>
        <p className="muted" style={{marginTop: 8, marginBottom: 12}}>
          Upload your resume PDF, paste a job description, accept smart suggestions, and export a polished version.
        </p>
        <div className="row gap">
          <Link href="/app" className="btn btn-primary">Try the demo</Link>
          <Link href="/login" className="btn">Log in</Link>
        </div>
      </section>

      <section className="card" style={{marginTop: 12}}>
        <div className="section-title">How it works</div>
        <ol style={{margin: 0, paddingLeft: 18}}>
          <li>Upload your resume PDF</li>
          <li>Paste a job posting or URL</li>
          <li>Accept suggested bullet improvements</li>
          <li>Export as PDF or DOCX</li>
        </ol>
      </section>
    </main>
  );
}



