import Link from "next/link";
import {
  Code2,
  Zap,
  Monitor,
  Layers,
  ArrowRight,
  Bot,
  Eye,
  Rocket,
  CheckCircle2,
} from "lucide-react";

const FEATURES = [
  {
    icon: Bot,
    title: "Multi-Agent AI",
    description:
      "6 specialized AI agents collaborate in parallel — Supervisor, Frontend, Backend, Database, DevOps, and QA — to build complete applications.",
  },
  {
    icon: Eye,
    title: "Real-time Preview",
    description:
      "Watch your app come to life in a sandboxed environment. Every build gets an instant live preview URL you can share.",
  },
  {
    icon: Rocket,
    title: "Instant Deploy",
    description:
      "From prompt to production in minutes. Docker configs generated automatically. One-click deploy to your infrastructure.",
  },
  {
    icon: Layers,
    title: "Full-Stack Output",
    description:
      "Not just frontend — get complete backends with APIs, database schemas, migrations, seed data, and deployment configs.",
  },
];

const PRICING = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Perfect for trying it out",
    features: ["5 projects/month", "Single agent mode", "Community support", "Basic templates"],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$20",
    period: "/month",
    description: "For serious builders",
    features: [
      "Unlimited projects",
      "Multi-agent pipeline",
      "Priority support",
      "Custom templates",
      "Team sharing",
    ],
    cta: "Start Pro Trial",
    highlighted: true,
  },
  {
    name: "Team",
    price: "$50",
    period: "/month",
    description: "For teams and agencies",
    features: [
      "Everything in Pro",
      "5 team members",
      "Custom AI models",
      "API access",
      "SSO / SAML",
      "Dedicated support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0B] text-zinc-200">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-[#1E1E22] bg-[#0A0A0B]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Code2 className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold">CodeSaaS</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">
              Features
            </a>
            <a href="#pricing" className="text-sm text-zinc-400 hover:text-white transition-colors">
              Pricing
            </a>
            <Link
              href="/auth"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pb-20 pt-24">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-600/5 to-transparent" />
        <div className="relative mx-auto max-w-4xl px-6 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5">
            <Zap className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-xs font-medium text-blue-300">
              Multi-Agent AI Code Generation
            </span>
          </div>

          <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
            Describe it.{" "}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              We build it.
            </span>
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-lg text-zinc-400 leading-relaxed">
            Turn natural language into production-ready web applications. Six AI agents
            work in parallel to generate frontend, backend, database, and deployment
            code — with live preview in seconds.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-600/25 hover:bg-blue-500 transition-all hover:shadow-blue-600/40"
            >
              Multi-Agent IDE <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/build"
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-emerald-600/25 hover:bg-emerald-500 transition-all hover:shadow-emerald-600/40"
            >
              Build & Host Free <Rocket className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* IDE Mockup */}
        <div className="mx-auto mt-16 max-w-5xl px-6">
          <div className="overflow-hidden rounded-xl border border-[#1E1E22] bg-[#111113] shadow-2xl shadow-black/50">
            <div className="flex items-center gap-2 border-b border-[#1E1E22] px-4 py-3">
              <div className="h-3 w-3 rounded-full bg-red-500/60" />
              <div className="h-3 w-3 rounded-full bg-amber-500/60" />
              <div className="h-3 w-3 rounded-full bg-emerald-500/60" />
              <span className="ml-3 text-xs text-zinc-500">CodeSaaS — IDE</span>
            </div>
            <div className="grid grid-cols-[200px_1fr] h-[320px]">
              {/* Fake sidebar */}
              <div className="border-r border-[#1E1E22] p-3 space-y-2">
                <p className="text-[10px] uppercase text-zinc-600 font-semibold">Agents</p>
                {["Supervisor", "Frontend", "Backend", "QA"].map((agent, i) => (
                  <div key={agent} className="flex items-center gap-2 rounded-md bg-[#1A1A1F] px-2 py-1.5">
                    <span className={`h-2 w-2 rounded-full ${i < 3 ? "bg-emerald-500" : "bg-blue-500 animate-pulse"}`} />
                    <span className="text-[11px] text-zinc-400">{agent}</span>
                  </div>
                ))}
              </div>
              {/* Fake editor */}
              <div className="p-4 font-mono text-[11px] text-zinc-500 leading-relaxed">
                <p><span className="text-purple-400">{"<!DOCTYPE"}</span> <span className="text-blue-400">html</span><span className="text-purple-400">{">"}</span></p>
                <p><span className="text-purple-400">{"<html"}</span> <span className="text-cyan-400">lang</span>=<span className="text-green-400">{'"en"'}</span><span className="text-purple-400">{">"}</span></p>
                <p><span className="text-purple-400">{"<head>"}</span></p>
                <p>{"  "}<span className="text-purple-400">{"<title>"}</span><span className="text-zinc-300">My SaaS App</span><span className="text-purple-400">{"</title>"}</span></p>
                <p>{"  "}<span className="text-purple-400">{"<script"}</span> <span className="text-cyan-400">src</span>=<span className="text-green-400">{'"https://cdn.tailwindcss.com"'}</span><span className="text-purple-400">{"></script>"}</span></p>
                <p><span className="text-purple-400">{"</head>"}</span></p>
                <p><span className="text-purple-400">{"<body"}</span> <span className="text-cyan-400">class</span>=<span className="text-green-400">{'"bg-gray-50"'}</span><span className="text-purple-400">{">"}</span></p>
                <p className="text-zinc-600 mt-2">{"  // "}AI-generated premium UI...</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-[#1E1E22] py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">Built for builders</h2>
            <p className="mt-4 text-lg text-zinc-500">
              Everything you need to go from idea to deployed app
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="group rounded-xl border border-[#1E1E22] bg-[#111113] p-6 transition-all hover:border-[#2A2A2E] hover:shadow-lg hover:shadow-blue-600/5"
                >
                  <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600/10">
                    <Icon className="h-5 w-5 text-blue-400" />
                  </div>
                  <h3 className="mb-2 font-semibold text-zinc-200">{feature.title}</h3>
                  <p className="text-sm leading-relaxed text-zinc-500">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-[#1E1E22] py-24">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">Simple pricing</h2>
            <p className="mt-4 text-lg text-zinc-500">
              Start free. Scale when you need to.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl border p-8 transition-all ${
                  plan.highlighted
                    ? "border-blue-500/50 bg-blue-600/5 shadow-lg shadow-blue-600/10"
                    : "border-[#1E1E22] bg-[#111113]"
                }`}
              >
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <p className="mt-1 text-sm text-zinc-500">{plan.description}</p>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-zinc-500">{plan.period}</span>
                </div>
                <ul className="mt-6 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-zinc-400">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/auth"
                  className={`mt-8 block w-full rounded-lg py-2.5 text-center text-sm font-medium transition-colors ${
                    plan.highlighted
                      ? "bg-blue-600 text-white hover:bg-blue-500"
                      : "bg-zinc-800 text-zinc-200 hover:bg-zinc-700"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1E1E22] py-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-blue-600">
              <Code2 className="h-3 w-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-zinc-400">CodeSaaS</span>
          </div>
          <p className="text-xs text-zinc-600">
            &copy; {new Date().getFullYear()} CodeSaaS. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
