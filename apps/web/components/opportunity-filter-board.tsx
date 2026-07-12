"use client";

import { useMemo, useState } from "react";

import { OpportunityCard } from "@/components/opportunity-card";
import { formatSourceName } from "@/lib/format";
import type { Opportunity, SourceDescriptor } from "@/lib/types";

type Intake = {
  id: string;
  label: string;
  year: "2026" | "2027";
  months: number[];
};

type OpportunityFilterBoardProps = {
  opportunities: Opportunity[];
  sources: SourceDescriptor[];
};

const TARGET_YEARS = ["2026", "2027"] as const;
const TARGET_INTAKES: Intake[] = [
  { id: "2026-fall", label: "Fall", year: "2026", months: [9, 10] },
  { id: "2027-spring", label: "Spring", year: "2027", months: [1, 2, 3] },
  { id: "2027-summer", label: "Summer", year: "2027", months: [6, 7] },
  { id: "2027-fall", label: "Fall", year: "2027", months: [9, 10] },
];

const MONTHS: Record<string, number> = {
  jan: 1,
  january: 1,
  feb: 2,
  february: 2,
  mar: 3,
  march: 3,
  jun: 6,
  june: 6,
  jul: 7,
  july: 7,
  sep: 9,
  sept: 9,
  september: 9,
  oct: 10,
  october: 10,
};

function parseStartDate(value: string | null): { year: string | null; month: number | null } {
  if (!value) {
    return { year: null, month: null };
  }

  const lowered = value.toLowerCase();
  const isoMatch = lowered.match(/\b(2026|2027)-(\d{1,2})(?:-\d{1,2})?\b/);
  if (isoMatch) {
    return { year: isoMatch[1], month: Number(isoMatch[2]) };
  }

  const yearMatch = lowered.match(/\b(2026|2027)\b/);
  const monthEntry = Object.entries(MONTHS).find(([name]) =>
    new RegExp(`\\b${name}\\b`).test(lowered),
  );

  return {
    year: yearMatch?.[1] ?? null,
    month: monthEntry?.[1] ?? null,
  };
}

function matchesYear(opportunity: Opportunity, year: string | null): boolean {
  if (!year) {
    return true;
  }
  return parseStartDate(opportunity.start_date_text).year === year;
}

function matchesIntake(opportunity: Opportunity, intake: Intake | null): boolean {
  if (!intake) {
    return true;
  }
  const parsed = parseStartDate(opportunity.start_date_text);
  return parsed.year === intake.year && parsed.month !== null && intake.months.includes(parsed.month);
}

function countMatching(items: Opportunity[], predicate: (item: Opportunity) => boolean): number {
  return items.filter(predicate).length;
}

export function OpportunityFilterBoard({ opportunities, sources }: OpportunityFilterBoardProps) {
  const [selectedYear, setSelectedYear] = useState<string | null>(null);
  const [selectedIntakeId, setSelectedIntakeId] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  const selectedIntake = TARGET_INTAKES.find((intake) => intake.id === selectedIntakeId) ?? null;
  const sourceNames = useMemo(
    () =>
      Array.from(
        new Set([
          ...sources.map((source) => source.source_name),
          ...opportunities.map((item) => item.source_name),
        ]),
      ).sort(),
    [opportunities, sources],
  );

  const yearScoped = opportunities.filter((item) => matchesYear(item, selectedYear));
  const intakeOptions = TARGET_INTAKES.filter((intake) => !selectedYear || intake.year === selectedYear);
  const intakeScoped = yearScoped.filter((item) => matchesIntake(item, selectedIntake));
  const filtered = intakeScoped.filter((item) => !selectedSource || item.source_name === selectedSource);

  const handleYear = (year: string | null) => {
    setSelectedYear(year);
    setSelectedIntakeId(null);
    setSelectedSource(null);
  };

  const handleIntake = (intakeId: string | null) => {
    setSelectedIntakeId(intakeId);
    setSelectedSource(null);
  };

  return (
    <>
      <div className="filter-board panel">
        <div className="filter-group">
          <div className="filter-label">Year</div>
          <div className="filter-options">
            <button
              className={`filter-option ${selectedYear === null ? "filter-option-active" : ""}`}
              onClick={() => handleYear(null)}
              type="button"
            >
              <span className="filter-count">{opportunities.length}</span>
              <span>All</span>
            </button>
            {TARGET_YEARS.map((year) => (
              <button
                className={`filter-option ${selectedYear === year ? "filter-option-active" : ""}`}
                key={year}
                onClick={() => handleYear(year)}
                type="button"
              >
                <span className="filter-count">
                  {countMatching(opportunities, (item) => matchesYear(item, year))}
                </span>
                <span>{year}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <div className="filter-label">Intake</div>
          <div className="filter-options">
            <button
              className={`filter-option ${selectedIntakeId === null ? "filter-option-active" : ""}`}
              onClick={() => handleIntake(null)}
              type="button"
            >
              <span className="filter-count">{yearScoped.length}</span>
              <span>All</span>
            </button>
            {intakeOptions.map((intake) => (
              <button
                className={`filter-option ${selectedIntakeId === intake.id ? "filter-option-active" : ""}`}
                key={intake.id}
                onClick={() => handleIntake(intake.id)}
                type="button"
              >
                <span className="filter-count">
                  {countMatching(yearScoped, (item) => matchesIntake(item, intake))}
                </span>
                <span>{selectedYear ? intake.label : `${intake.year} ${intake.label}`}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <div className="filter-label">Website</div>
          <div className="filter-options">
            <button
              className={`filter-option ${selectedSource === null ? "filter-option-active" : ""}`}
              onClick={() => setSelectedSource(null)}
              type="button"
            >
              <span className="filter-count">{intakeScoped.length}</span>
              <span>All</span>
            </button>
            {sourceNames.map((sourceName) => (
              <button
                className={`filter-option ${selectedSource === sourceName ? "filter-option-active" : ""}`}
                key={sourceName}
                onClick={() => setSelectedSource(sourceName)}
                type="button"
              >
                <span className="filter-count">
                  {countMatching(intakeScoped, (item) => item.source_name === sourceName)}
                </span>
                <span>{formatSourceName(sourceName)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid">
        {filtered.length > 0 ? (
          filtered.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))
        ) : (
          <div className="panel empty-state">
            No active opportunities match those filters yet.
          </div>
        )}
      </div>
    </>
  );
}
