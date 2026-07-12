"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { setAppliedState } from "@/lib/api";

type ApplyToggleProps = {
  opportunityId: number;
  isApplied: boolean;
};

export function ApplyToggle({
  opportunityId,
  isApplied,
}: ApplyToggleProps) {
  const router = useRouter();
  const [applied, setApplied] = useState(isApplied);
  const [isPending, startTransition] = useTransition();

  const handleClick = () => {
    const nextValue = !applied;
    startTransition(async () => {
      try {
        await setAppliedState(opportunityId, nextValue);
        setApplied(nextValue);
        router.refresh();
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
