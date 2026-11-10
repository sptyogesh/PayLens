"""Report sections in reading order. Each takes ReportData and returns ReportLab flowables."""

from app.reports.sections.breakdowns import breakdowns
from app.reports.sections.fira import fira
from app.reports.sections.header import header
from app.reports.sections.income import income
from app.reports.sections.leakage import leakage
from app.reports.sections.notes import notes
from app.reports.sections.summary import summary

SECTIONS = (header, summary, income, leakage, breakdowns, fira, notes)

__all__ = ["SECTIONS"]
