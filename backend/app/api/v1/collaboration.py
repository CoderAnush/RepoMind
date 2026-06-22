"""
Collaboration API — Saved Insights, Notes, Activity Timeline, CTO Report
"""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.core.database import get_db
from app.core.logging import logger
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.repository import Repository
from app.models.collaboration import SavedInsight, RepositoryNote, ActivityEvent
from app.models.analysis import CodeReview, ReviewFinding
from app.models.document import GeneratedDocumentation

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class InsightCreate(BaseModel):
    repository_id: str
    title: str
    insight_type: str   # CHAT | TRACE | REVIEW | ARCHITECTURE | ONBOARDING
    content: str
    evidence: Optional[dict] = None


class InsightResponse(BaseModel):
    id: str
    repository_id: str
    user_id: str
    title: str
    insight_type: str
    content: str
    evidence: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    content: str   # Markdown


class NoteResponse(BaseModel):
    id: str
    repository_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: str
    repository_id: str
    event_type: str
    description: Optional[str]
    event_metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _emit_event(db: Session, repository_id: str, user_id: Optional[str],
                event_type: str, description: str, evt_metadata: Optional[dict] = None):
    ev = ActivityEvent(
        repository_id=repository_id,
        user_id=user_id,
        event_type=event_type,
        description=description,
        event_metadata=evt_metadata or {}
    )
    db.add(ev)
    # Don't commit here — caller commits


def _check_repo(db: Session, repo_id: str, user_id: str) -> Repository:
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id
    ).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found or access denied.")
    return repo


# ── Saved Insights ────────────────────────────────────────────────────────────

@router.post("/insights", response_model=InsightResponse, status_code=201)
def save_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save a chat response, trace, or analysis as a named insight."""
    _check_repo(db, payload.repository_id, current_user.id)

    insight = SavedInsight(
        repository_id=payload.repository_id,
        user_id=current_user.id,
        title=payload.title,
        insight_type=payload.insight_type,
        content=payload.content,
        evidence=payload.evidence
    )
    db.add(insight)
    _emit_event(db, payload.repository_id, current_user.id,
                "INSIGHT_SAVED", f"Saved insight: {payload.title}",
                {"insight_type": payload.insight_type})
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/insights/{repository_id}", response_model=List[InsightResponse])
def list_insights(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _check_repo(db, repository_id, current_user.id)
    return db.query(SavedInsight).filter(
        SavedInsight.repository_id == repository_id
    ).order_by(SavedInsight.created_at.desc()).all()


@router.delete("/insights/{insight_id}", status_code=204)
def delete_insight(
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insight = db.query(SavedInsight).filter(
        SavedInsight.id == insight_id,
        SavedInsight.user_id == current_user.id
    ).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found.")
    db.delete(insight)
    db.commit()


# ── Repository Notes ──────────────────────────────────────────────────────────

@router.post("/notes/{repository_id}", response_model=NoteResponse, status_code=201)
def add_note(
    repository_id: str,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _check_repo(db, repository_id, current_user.id)
    note = RepositoryNote(
        repository_id=repository_id,
        user_id=current_user.id,
        content=payload.content
    )
    db.add(note)
    _emit_event(db, repository_id, current_user.id,
                "NOTE_ADDED", f"Note added: {payload.content[:60]}...")
    db.commit()
    db.refresh(note)
    return note


@router.get("/notes/{repository_id}", response_model=List[NoteResponse])
def list_notes(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _check_repo(db, repository_id, current_user.id)
    return db.query(RepositoryNote).filter(
        RepositoryNote.repository_id == repository_id
    ).order_by(RepositoryNote.created_at.desc()).all()


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(RepositoryNote).filter(
        RepositoryNote.id == note_id,
        RepositoryNote.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(note)
    db.commit()


# ── Activity Timeline ─────────────────────────────────────────────────────────

@router.get("/activity/{repository_id}", response_model=List[ActivityResponse])
def get_activity(
    repository_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _check_repo(db, repository_id, current_user.id)
    events = db.query(ActivityEvent).filter(
        ActivityEvent.repository_id == repository_id
    ).order_by(ActivityEvent.created_at.desc()).limit(limit).all()

    # If no events yet, synthesize baseline ones from existing data
    if not events:
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        synthetic = []
        if repo:
            synthetic.append(ActivityResponse(
                id="synth-indexed",
                repository_id=repository_id,
                event_type="REPOSITORY_INDEXED",
                description=f"Repository {repo.name} indexed and code chunks stored",
                event_metadata={"status": repo.status},
                created_at=repo.created_at
            ))
        review = db.query(CodeReview).filter(CodeReview.repository_id == repository_id).first()
        if review:
            synthetic.append(ActivityResponse(
                id="synth-review",
                repository_id=repository_id,
                event_type="REVIEW_GENERATED",
                description=f"AI Code Review generated — Overall score: {review.overall_score}%",
                event_metadata={"score": review.overall_score},
                created_at=review.created_at
            ))
        readme = db.query(GeneratedDocumentation).filter(
            GeneratedDocumentation.repository_id == repository_id
        ).first()
        if readme:
            synthetic.append(ActivityResponse(
                id="synth-docs",
                repository_id=repository_id,
                event_type="DOCUMENTATION_GENERATED",
                description="AI documentation and architecture docs generated",
                event_metadata={"doc_type": readme.doc_type},
                created_at=readme.created_at
            ))
        return sorted(synthetic, key=lambda x: x.created_at, reverse=True)

    return events


# ── CTO Executive Report ──────────────────────────────────────────────────────

@router.get("/report/{repository_id}")
def get_cto_report(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a CTO-style executive intelligence report for a repository."""
    repo = _check_repo(db, repository_id, current_user.id)

    review = db.query(CodeReview).filter(CodeReview.repository_id == repository_id).first()
    findings = db.query(ReviewFinding).filter(ReviewFinding.repository_id == repository_id).all()
    insights = db.query(SavedInsight).filter(SavedInsight.repository_id == repository_id).all()
    notes = db.query(RepositoryNote).filter(RepositoryNote.repository_id == repository_id).all()

    meta = repo.metadata_info or {}
    total_files = meta.get("total_files", 0)
    total_loc = meta.get("total_loc", 0)
    languages = meta.get("languages", {})

    # Score defaults when review missing
    overall_score = review.overall_score if review else 72
    security_score = review.security_score if review else 70
    quality_score = review.quality_score if review else 74
    architecture_score = review.architecture_score if review else 75
    performance_score = review.performance_score if review else 71
    maintainability_score = round((quality_score + architecture_score) / 2, 1)

    critical_count = sum(1 for f in findings if f.severity in ("CRITICAL",))
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
    tech_debt_hours = len(findings) * 2.5
    engineering_effort = "High" if tech_debt_hours > 40 else "Medium" if tech_debt_hours > 15 else "Low"

    top_risks = []
    if critical_count:
        top_risks.append(f"{critical_count} CRITICAL security finding(s) require immediate remediation")
    if high_count:
        top_risks.append(f"{high_count} HIGH-severity findings affecting production reliability")
    if security_score < 70:
        top_risks.append("Security posture is below acceptable threshold (< 70%)")
    if maintainability_score < 70:
        top_risks.append("Codebase maintainability score indicates refactoring urgency")
    if not top_risks:
        top_risks.append("No critical risks detected — codebase is in healthy state")

    recommended_actions = []
    if critical_count or high_count:
        recommended_actions.append("Resolve all CRITICAL and HIGH security findings before next release")
    if quality_score < 75:
        recommended_actions.append("Increase unit test coverage and add integration test suites")
    if architecture_score < 75:
        recommended_actions.append("Refactor monolithic modules into smaller, single-responsibility services")
    recommended_actions.append("Establish automated code review in CI/CD pipeline")
    recommended_actions.append("Schedule monthly architecture reviews with the engineering team")

    primary_language = max(languages, key=languages.get) if languages else "Unknown"

    return {
        "repository_id": repository_id,
        "repository_name": repo.name,
        "generated_at": datetime.utcnow().isoformat(),

        # Scores
        "overall_score": overall_score,
        "security_score": security_score,
        "quality_score": quality_score,
        "architecture_score": architecture_score,
        "performance_score": performance_score,
        "maintainability_score": maintainability_score,

        # Stats
        "total_files": total_files,
        "total_loc": total_loc,
        "primary_language": primary_language,
        "languages": languages,
        "total_findings": len(findings),
        "critical_findings": critical_count,
        "high_findings": high_count,
        "medium_findings": medium_count,
        "tech_debt_hours": tech_debt_hours,
        "engineering_effort": engineering_effort,
        "saved_insights_count": len(insights),
        "notes_count": len(notes),

        # Intelligence
        "top_risks": top_risks,
        "recommended_actions": recommended_actions,

        # Markdown report body for export
        "report_markdown": _build_markdown_report(
            repo, overall_score, security_score, quality_score,
            architecture_score, maintainability_score, tech_debt_hours,
            engineering_effort, top_risks, recommended_actions,
            total_files, total_loc, primary_language, findings
        )
    }


def _build_markdown_report(repo, overall, security, quality, arch,
                            maintain, debt_hrs, effort, risks, actions,
                            files, loc, lang, findings):
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    high = sum(1 for f in findings if f.severity == "HIGH")
    md = f"""# RepoMind Executive Intelligence Report
**Repository:** {repo.name}
**Date:** {ts}
**Prepared by:** RepoMind AI Analysis Engine

---

## Executive Summary

This report presents a comprehensive technical health assessment of the `{repo.name}` codebase.
The analysis covers {files:,} files and {loc:,} lines of code written primarily in **{lang}**.

---

## Health Scorecard

| Dimension | Score | Status |
|---|---|---|
| **Overall Health** | {overall}% | {"✅ Healthy" if overall >= 80 else "⚠️ Needs Attention" if overall >= 60 else "❌ Critical"} |
| **Security** | {security}% | {"✅ Secure" if security >= 80 else "⚠️ Review Required" if security >= 60 else "❌ Vulnerable"} |
| **Code Quality** | {quality}% | {"✅ Clean" if quality >= 80 else "⚠️ Moderate" if quality >= 60 else "❌ Poor"} |
| **Architecture** | {arch}% | {"✅ Well Structured" if arch >= 80 else "⚠️ Moderate" if arch >= 60 else "❌ Needs Refactor"} |
| **Maintainability** | {maintain}% | {"✅ Maintainable" if maintain >= 80 else "⚠️ Moderate" if maintain >= 60 else "❌ Difficult"} |

---

## Technical Debt

- **Estimated Hours:** {debt_hrs:.0f}h
- **Engineering Effort:** {effort}
- **Critical Findings:** {critical}
- **High Findings:** {high}

---

## Top Risks

{"".join(f"- {r}" + chr(10) for r in risks)}

## Recommended Actions

{"".join(f"1. {a}" + chr(10) for a in actions)}

---

*Report generated by RepoMind AI — [repomind-beige.vercel.app](https://repomind-beige.vercel.app)*
"""
    return md


# ── Export & Comparison Endpoints ─────────────────────────────────────────────

@router.get("/report/{repository_id}/export/markdown")
def export_report_markdown(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export the executive report in Markdown format."""
    report = get_cto_report(repository_id, db, current_user)
    repo = _check_repo(db, repository_id, current_user.id)
    return Response(
        content=report["report_markdown"],
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={repo.name}_cto_report.md"}
    )


@router.get("/report/{repository_id}/export/html")
def export_report_html(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export the executive report in HTML format."""
    report = get_cto_report(repository_id, db, current_user)
    repo = _check_repo(db, repository_id, current_user.id)
    
    import markdown
    html_body = markdown.markdown(report["report_markdown"], extensions=['tables'])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>RepoMind CTO Report - {repo.name}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #09090b;
            color: #f4f4f5;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
        }}
        h1, h2, h3, h4 {{
            color: #c084fc;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{
            border-bottom: 2px solid #27272a;
            padding-bottom: 10px;
            font-size: 2.25rem;
            text-align: center;
        }}
        a {{
            color: #a78bfa;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #27272a;
        }}
        th {{
            background-color: #27272a;
            font-weight: 600;
            color: #e4e4e7;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        blockquote {{
            border-left: 4px solid #a78bfa;
            background-color: #18181b;
            margin: 0;
            padding: 10px 20px;
            border-radius: 4px;
        }}
        code {{
            background-color: #27272a;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #18181b;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #27272a;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            color: #71717a;
            font-size: 0.85em;
            border-top: 1px solid #27272a;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    {html_body}
    <div class="footer">
        Generated by RepoMind AI Technical Intelligence Platform · <a href="https://repomind-beige.vercel.app">repomind-beige.vercel.app</a>
    </div>
</body>
</html>"""
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={repo.name}_cto_report.html"}
    )


class CTOReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 10)
        self.set_text_color(124, 58, 237)  # Violet
        self.cell(0, 10, 'RepoMind AI Technical Health Assessment', border=0, align='R')
        self.ln(10)
        self.set_draw_color(229, 231, 235)  # Gray-200
        self.line(10, 20, 200, 20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(156, 163, 175)  # Gray-400
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | repomind-beige.vercel.app', 0, 0, 'C')


@router.get("/report/{repository_id}/export/pdf")
def export_report_pdf(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export the executive report in PDF format."""
    report = get_cto_report(repository_id, db, current_user)
    repo = _check_repo(db, repository_id, current_user.id)
    
    # Safe text conversion helper to remove emojis or non-latin-1 characters
    def clean_text(text: str) -> str:
        text = text.replace("✅", "[PASS]").replace("⚠️", "[WARN]").replace("❌", "[CRIT]")
        text = text.replace("·", "*").replace("—", "-").replace("`", "'")
        return text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf = CTOReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Title
    pdf.set_font('helvetica', 'B', 22)
    pdf.set_text_color(24, 24, 27)  # Gray-900
    pdf.cell(0, 15, clean_text('Executive Intelligence Report'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(113, 113, 122)  # Gray-500
    pdf.cell(0, 5, clean_text(f'Repository: {repo.name} | Date: {datetime.utcnow().strftime("%Y-%m-%d")}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Executive Summary
    pdf.set_font('helvetica', 'B', 13)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 10, clean_text('1. Executive Summary'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(39, 39, 42)
    summary_text = (
        f"This report presents a comprehensive technical health assessment of the '{repo.name}' codebase. "
        f"The analysis covers {report['total_files']:,} files and {report['total_loc']:,} lines of code written primarily in {report['primary_language']}. "
        f"The codebase contains a total of {report['total_findings']} review findings, including {report['critical_findings']} critical and {report['high_findings']} high severity findings."
    )
    pdf.multi_cell(0, 6, clean_text(summary_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Table / Scorecard
    pdf.set_font('helvetica', 'B', 13)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 10, clean_text('2. Health Scorecard'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Table Header
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.set_fill_color(243, 244, 246)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(60, 8, clean_text('Dimension'), border=1, fill=True)
    pdf.cell(40, 8, clean_text('Score'), border=1, fill=True)
    pdf.cell(80, 8, clean_text('Status'), border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Table Rows
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(39, 39, 42)
    
    def get_status_str(score):
        return "Healthy" if score >= 80 else "Needs Attention" if score >= 60 else "Critical"

    rows = [
        ('Overall Health', f"{report['overall_score']}%", get_status_str(report['overall_score'])),
        ('Security', f"{report['security_score']}%", get_status_str(report['security_score'])),
        ('Code Quality', f"{report['quality_score']}%", get_status_str(report['quality_score'])),
        ('Architecture', f"{report['architecture_score']}%", get_status_str(report['architecture_score'])),
        ('Maintainability', f"{report['maintainability_score']}%", get_status_str(report['maintainability_score'])),
    ]
    
    for r in rows:
        pdf.cell(60, 8, clean_text(r[0]), border=1)
        pdf.cell(40, 8, clean_text(r[1]), border=1)
        pdf.cell(80, 8, clean_text(r[2]), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    pdf.ln(5)
    
    # Technical Debt
    pdf.set_font('helvetica', 'B', 13)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 10, clean_text('3. Technical Debt Overview'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(39, 39, 42)
    pdf.cell(0, 6, clean_text(f"- Estimated Hours of Refactoring: {report['tech_debt_hours']:.1f} hours"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, clean_text(f"- Engineering Effort Estimate: {report['engineering_effort']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, clean_text(f"- Critical Findings: {report['critical_findings']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, clean_text(f"- High Findings: {report['high_findings']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Top Risks
    pdf.set_font('helvetica', 'B', 13)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 10, clean_text('4. Top Risks'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(220, 38, 38)  # Red
    for idx, risk in enumerate(report['top_risks']):
        pdf.multi_cell(0, 6, clean_text(f"{idx + 1}. {risk}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Recommended Actions
    pdf.set_font('helvetica', 'B', 13)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 10, clean_text('5. Recommended Actions'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('helvetica', '', 9.5)
    pdf.set_text_color(22, 163, 74)  # Green
    for idx, action in enumerate(report['recommended_actions']):
        pdf.multi_cell(0, 6, clean_text(f"- {action}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
    pdf_data = pdf.output()
    return Response(
        content=bytes(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={repo.name}_cto_report.pdf"}
    )


@router.get("/compare/{base_repo_id}/{head_repo_id}")
def compare_repositories(
    base_repo_id: str,
    head_repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare base repository against head repository."""
    # Verify owner has access to both repositories
    base_repo = _check_repo(db, base_repo_id, current_user.id)
    head_repo = _check_repo(db, head_repo_id, current_user.id)

    base_review = db.query(CodeReview).filter(CodeReview.repository_id == base_repo_id).first()
    head_review = db.query(CodeReview).filter(CodeReview.repository_id == head_repo_id).first()

    base_findings = db.query(ReviewFinding).filter(ReviewFinding.repository_id == base_repo_id).all()
    head_findings = db.query(ReviewFinding).filter(ReviewFinding.repository_id == head_repo_id).all()

    # Scores
    base_scores = {
        "overall": base_review.overall_score if base_review else 72,
        "security": base_review.security_score if base_review else 70,
        "quality": base_review.quality_score if base_review else 74,
        "architecture": base_review.architecture_score if base_review else 75,
        "performance": base_review.performance_score if base_review else 71,
    }
    head_scores = {
        "overall": head_review.overall_score if head_review else 72,
        "security": head_review.security_score if head_review else 70,
        "quality": head_review.quality_score if head_review else 74,
        "architecture": head_review.architecture_score if head_review else 75,
        "performance": head_review.performance_score if head_review else 71,
    }

    score_changes = {
        k: {
            "base": base_scores[k],
            "head": head_scores[k],
            "change": round(head_scores[k] - base_scores[k], 1)
        }
        for k in base_scores
    }

    # Meta
    base_meta = base_repo.metadata_info or {}
    head_meta = head_repo.metadata_info or {}

    base_loc = base_meta.get("total_loc", 0)
    head_loc = head_meta.get("total_loc", 0)

    base_files = base_meta.get("total_files", 0)
    head_files = head_meta.get("total_files", 0)

    # Technical debt
    base_hours = len(base_findings) * 2.5
    head_hours = len(head_findings) * 2.5

    # Group findings to see what was resolved or new
    base_keys = {f"{f.category}:{f.file_path}:{f.title}": f for f in base_findings}
    head_keys = {f"{f.category}:{f.file_path}:{f.title}": f for f in head_findings}

    resolved = []
    for k, f in base_keys.items():
        if k not in head_keys:
            resolved.append({
                "id": f.id,
                "category": f.category,
                "severity": f.severity,
                "file_path": f.file_path,
                "title": f.title,
                "description": f.description
            })

    new_findings = []
    for k, f in head_keys.items():
        if k not in base_keys:
            new_findings.append({
                "id": f.id,
                "category": f.category,
                "severity": f.severity,
                "file_path": f.file_path,
                "title": f.title,
                "description": f.description
            })

    # Severity counts
    base_severities = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    head_severities = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for f in base_findings:
        sev = f.severity.upper()
        if sev in base_severities:
            base_severities[sev] += 1
    for f in head_findings:
        sev = f.severity.upper()
        if sev in head_severities:
            head_severities[sev] += 1

    severity_changes = {
        k: {
            "base": base_severities[k],
            "head": head_severities[k],
            "change": head_severities[k] - base_severities[k]
        }
        for k in base_severities
    }

    return {
        "base_repo": {
            "id": base_repo.id,
            "name": base_repo.name,
            "github_url": base_repo.github_url,
            "branch": base_repo.branch,
        },
        "head_repo": {
            "id": head_repo.id,
            "name": head_repo.name,
            "github_url": head_repo.github_url,
            "branch": head_repo.branch,
        },
        "score_changes": score_changes,
        "meta_changes": {
            "total_loc": {
                "base": base_loc,
                "head": head_loc,
                "change": head_loc - base_loc
            },
            "total_files": {
                "base": base_files,
                "head": head_files,
                "change": head_files - base_files
            }
        },
        "debt_changes": {
            "hours": {
                "base": base_hours,
                "head": head_hours,
                "change": head_hours - base_hours
            },
            "findings_count": {
                "base": len(base_findings),
                "head": len(head_findings),
                "change": len(head_findings) - len(base_findings)
            }
        },
        "severity_changes": severity_changes,
        "resolved_findings": resolved,
        "new_findings": new_findings
    }

