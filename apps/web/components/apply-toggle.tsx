"use client";

import { useState, useTransition } from "react";

import { setAppliedState } from "@/lib/api";
import type { Opportunity } from "@/lib/types";

type ApplyToggleProps = {
  opportunityId: number;
  isApplied: boolean;
  onOpportunityUpdated?: (opportunity: Opportunity) => void;
};

export function ApplyToggle({
  opportunityId,
  isApplied,
  onOpportunityUpdated,
}: ApplyToggleProps) {
  const [applied, setApplied] = useState(isApplied);
  const [isPending, startTransition] = useTransition();

  const handleClick = () => {
    const nextValue = !applied;
    startTransition(async () => {
      try {
        const updated = await setAppliedState(opportunityId, nextValue);
        setApplied(Boolean(updated.tracking?.is_applied));
        onOpportunityUpdated?.(updated);
      } catch (error) {
        console.error(error);
      }
    });
  };

  return (
    <button
      className={`button ${applied ? "button-success" : "button-primary"}`}
      onClick={handleClick}
      disabled={isPending}
      type="button"
    >
      {isPending
        ? "Updating..."
        : applied
          ? "Applied: marked green"
          : "Mark as applied"}
    </button>
  );
}
