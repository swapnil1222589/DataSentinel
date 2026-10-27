"""Report generation and export serialization engine (JSON, CSV, and standalone HTML)."""

import datetime
import json
from typing import Any, Dict, List, Optional

import pandas as pd

from datasentinel.schemas.findings import DatasetMetadata, IssueFinding, QualityScoreResult
from datasentinel.schemas.rules import RuleEvaluationResult
from datasentinel.utils.formatting import (
    get_score_color,
    get_severity_color,
)


def build_report_data(
    metadata: DatasetMetadata,
    quality_score: QualityScoreResult,
    findings: List[IssueFinding],
    missing_summary: Dict[str, Any],
    duplicate_summary: Dict[str, Any],
    type_summary: Dict[str, Any],
    outlier_summary: Dict[str, Any],
    rule_results: Optional[List[RuleEvaluationResult]] = None,
    drift_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compile comprehensive structured report dictionary."""
    return {
        "report_id": f"ds_report_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "application": "DataSentinel Open-Source Platform",
        "metadata": metadata.to_dict(),
        "quality_score": quality_score.to_dict(),
        "findings_count": len(findings),
        "findings_by_severity": {
            "critical": sum(1 for f in findings if f.severity.value == "critical"),
            "high": sum(1 for f in findings if f.severity.value == "high"),
            "medium": sum(1 for f in findings if f.severity.value == "medium"),
            "low": sum(1 for f in findings if f.severity.value == "low"),
            "info": sum(1 for f in findings if f.severity.value == "info"),
        },
        "findings": [f.to_dict() for f in findings],
        "missing_summary": {
            "total_cells": missing_summary.get("total_cells", 0),
            "total_missing_cells": missing_summary.get("total_missing_cells", 0),
            "overall_missing_pct": missing_summary.get("overall_missing_pct", 0.0),
            "columns_with_missing": missing_summary.get("columns_with_missing", 0),
        },
        "duplicate_summary": {
            "total_rows": duplicate_summary.get("total_rows", 0),
            "duplicate_count": duplicate_summary.get("duplicate_count", 0),
            "duplicate_pct": duplicate_summary.get("duplicate_pct", 0.0),
        },
        "type_summary": {
            "constant_columns": type_summary.get("constant_columns", []),
            "numeric_stored_as_text": type_summary.get("numeric_stored_as_text", []),
            "mixed_type_columns": type_summary.get("mixed_type_columns", []),
            "whitespace_issues": type_summary.get("whitespace_issues", []),
            "duplicate_columns": type_summary.get("duplicate_columns", []),
        },
        "validation_rules": [r.to_dict() for r in (rule_results or [])],
        "drift_summary": drift_summary if drift_summary else None,
        "limitations": [
            "DataSentinel performs deterministic local quality checks and statistical heuristic scoring.",
            "Local memory limits apply based on host RAM; datasets exceeding RAM will incur performance impact.",
            "Statistical outliers and drift flags represent distribution shifts requiring human domain verification.",
        ],
    }


def export_json_report(report_data: Dict[str, Any]) -> str:
    """Serialize report dictionary to formatted JSON string."""
    return json.dumps(report_data, indent=2, default=str)


def export_csv_issues(findings: List[IssueFinding]) -> str:
    """Serialize issues into a formatted CSV string."""
    rows = []
    for f in findings:
        rows.append(
            {
                "Severity": f.severity.value.upper(),
                "Dimension": f.dimension.value.title(),
                "Column": f.column or "Dataset-level",
                "Issue Type": f.issue_type,
                "Title": f.title,
                "Description": f.description,
                "Affected Count": f.affected_count,
                "Affected %": f"{f.affected_percentage:.2f}%",
                "Suggested Action": f.suggested_action,
            }
        )
    df_issues = pd.DataFrame(rows)
    return df_issues.to_csv(index=False)


def export_html_report(report_data: Dict[str, Any]) -> str:
    """Generate a clean, standalone, responsive HTML report."""
    meta = report_data.get("metadata", {})
    qs = report_data.get("quality_score", {})
    score = qs.get("overall_score", 0.0)
    grade = qs.get("grade", "N/A")
    dim_scores = qs.get("dimension_scores", {})
    findings = report_data.get("findings", [])
    report_data.get("findings_by_severity", {})

    findings_rows = ""
    for f in findings:
        sev = f.get("severity", "info").lower()
        color = get_severity_color(sev)
        findings_rows += f"""
        <tr>
            <td><span style="background:{color}22; color:{color}; border:1px solid {color}55; padding:3px 8px; border-radius:4px; font-weight:600; text-transform:uppercase; font-size:11px;">{sev}</span></td>
            <td><strong>{f.get("column", "N/A")}</strong></td>
            <td>{f.get("title", "")}</td>
            <td style="color:#94a3b8; font-size:13px;">{f.get("description", "")}</td>
            <td>{f.get("affected_count", 0):,} ({f.get("affected_percentage", 0.0):.1f}%)</td>
            <td style="font-size:13px; color:#38bdf8;">{f.get("suggested_action", "")}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataSentinel Quality Audit Report - {meta.get("filename", "Dataset")}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0b111e;
            color: #e2e8f0;
            line-height: 1.5;
            padding: 32px 20px;
        }}
        .container {{ max-width: 1140px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #151f32 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 28px 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .brand {{ display: flex; align-items: center; gap: 12px; }}
        .brand-badge {{
            background: #3b82f6;
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 0.5px;
        }}
        .score-hero {{
            display: flex;
            align-items: center;
            gap: 20px;
            background: #0b111e;
            padding: 16px 24px;
            border-radius: 10px;
            border: 1px solid #334155;
        }}
        .score-val {{ font-size: 44px; font-weight: 800; color: {get_score_color(score)}; line-height: 1; }}
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #151f32;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 20px;
        }}
        .card-label {{ font-size: 12px; text-transform: uppercase; color: #94a3b8; font-weight: 600; margin-bottom: 6px; }}
        .card-val {{ font-size: 26px; font-weight: 700; color: #f8fafc; }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            margin: 28px 0 14px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #151f32;
            border: 1px solid #334155;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #1e293b;
        }}
        th {{
            background: #1e293b;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .dim-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .dim-card {{
            background: #151f32;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .dim-score {{ font-size: 28px; font-weight: 700; margin-top: 4px; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #1e293b;
            color: #64748b;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="brand">
                    <span class="brand-badge">DATASENTINEL</span>
                    <span style="color:#94a3b8; font-size:13px;">Dataset Quality & Observability Platform</span>
                </div>
                <h1 style="font-size:24px; margin-top:8px; color:#fff;">Quality Audit: {meta.get("filename", "Dataset")}</h1>
                <p style="color:#94a3b8; font-size:13px; margin-top:4px;">Generated on {report_data.get("generated_at", "UTC")}</p>
            </div>
            <div class="score-hero">
                <div>
                    <div style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:600;">Overall Score</div>
                    <div class="score-val">{score:.1f}</div>
                </div>
                <div style="border-left:1px solid #334155; padding-left:16px;">
                    <div style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:600;">Grade</div>
                    <div style="font-size:32px; font-weight:800; color:{get_score_color(score)};">{grade}</div>
                </div>
            </div>
        </div>

        <div class="grid-cards">
            <div class="card">
                <div class="card-label">Total Records</div>
                <div class="card-val">{meta.get("row_count", 0):,}</div>
            </div>
            <div class="card">
                <div class="card-label">Columns</div>
                <div class="card-val">{meta.get("column_count", 0):,}</div>
            </div>
            <div class="card">
                <div class="card-label">Missing Cells</div>
                <div class="card-val">{report_data.get("missing_summary", {}).get("overall_missing_pct", 0.0):.1f}%</div>
            </div>
            <div class="card">
                <div class="card-label">Duplicate Rows</div>
                <div class="card-val">{report_data.get("duplicate_summary", {}).get("duplicate_count", 0):,}</div>
            </div>
            <div class="card">
                <div class="card-label">Detected Issues</div>
                <div class="card-val" style="color:#f59e0b;">{report_data.get("findings_count", 0)}</div>
            </div>
        </div>

        <h2 class="section-title">Dimension Breakdown</h2>
        <div class="dim-grid">
            <div class="dim-card">
                <div class="card-label">Completeness</div>
                <div class="dim-score" style="color:{get_score_color(dim_scores.get("completeness", 0))};">{dim_scores.get("completeness", 0):.1f}</div>
            </div>
            <div class="dim-card">
                <div class="card-label">Validity</div>
                <div class="dim-score" style="color:{get_score_color(dim_scores.get("validity", 0))};">{dim_scores.get("validity", 0):.1f}</div>
            </div>
            <div class="dim-card">
                <div class="card-label">Uniqueness</div>
                <div class="dim-score" style="color:{get_score_color(dim_scores.get("uniqueness", 0))};">{dim_scores.get("uniqueness", 0):.1f}</div>
            </div>
            <div class="dim-card">
                <div class="card-label">Consistency</div>
                <div class="dim-score" style="color:{get_score_color(dim_scores.get("consistency", 0))};">{dim_scores.get("consistency", 0):.1f}</div>
            </div>
        </div>

        <h2 class="section-title">Detected Quality Findings & Remediations ({len(findings)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Column</th>
                    <th>Issue</th>
                    <th>Description</th>
                    <th>Impact</th>
                    <th>Suggested Action</th>
                </tr>
            </thead>
            <tbody>
                {findings_rows if findings_rows else '<tr><td colspan="6" style="text-align:center; color:#10b981; padding:24px;">No quality issues detected! Dataset meets all checks.</td></tr>'}
            </tbody>
        </table>

        <div class="footer">
            DataSentinel Open-Source Platform &bull; Deterministic Data Observability &bull; "Know your data before your model does."
        </div>
    </div>
</body>
</html>
"""
    return html
