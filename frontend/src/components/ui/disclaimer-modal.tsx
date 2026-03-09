"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface DisclaimerModalProps {
  userId: string;
  onComplete: () => void;
}

const DISCLAIMERS = [
  {
    id: 1,
    title: "Early Access MVP",
    description: "Important Notice",
    content:
      "This is an early MVP (Minimum Viable Product) version of CodeSaaS. The AI-generated results may not always be accurate or production-ready. Please review all generated code carefully before use.",
    icon: "⚠️",
  },
  {
    id: 2,
    title: "Project Limitation",
    description: "Account Restriction",
    content:
      "During this early access period, each account is limited to creating only 1 project. Choose your project wisely, as this limitation helps us maintain service quality for all users.",
    icon: "📁",
  },
];

export function DisclaimerModal({ userId, onComplete }: DisclaimerModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [visible, setVisible] = useState(false);

  const storageKey = `disclaimers_seen_${userId}`;

  useEffect(() => {
    // Check if user has already seen disclaimers
    const hasSeen = localStorage.getItem(storageKey);
    if (!hasSeen) {
      setVisible(true);
    } else {
      onComplete();
    }
  }, [storageKey, onComplete]);

  const handleNext = () => {
    if (currentStep < DISCLAIMERS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      // Mark disclaimers as seen
      localStorage.setItem(storageKey, "true");
      setVisible(false);
      onComplete();
    }
  };

  if (!visible) {
    return null;
  }

  const disclaimer = DISCLAIMERS[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <Card className="w-full max-w-md mx-4 border-zinc-800 bg-zinc-900">
        <CardHeader className="text-center">
          <div className="text-4xl mb-2">{disclaimer.icon}</div>
          <CardTitle className="text-xl text-zinc-100">
            {disclaimer.title}
          </CardTitle>
          <CardDescription className="text-zinc-400">
            {disclaimer.description}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-zinc-300 text-center leading-relaxed">
            {disclaimer.content}
          </p>
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button
            onClick={handleNext}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {currentStep < DISCLAIMERS.length - 1
              ? "I Understand, Continue"
              : "I Understand, Get Started"}
          </Button>
          <div className="flex gap-1 justify-center">
            {DISCLAIMERS.map((_, index) => (
              <div
                key={index}
                className={`h-1.5 w-6 rounded-full transition-colors ${
                  index === currentStep ? "bg-blue-500" : "bg-zinc-700"
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-zinc-500 text-center">
            Step {currentStep + 1} of {DISCLAIMERS.length}
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
