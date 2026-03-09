"""Shared design quality prompt appended to all code-generating agents."""

DESIGN_QUALITY_PROMPT = """
## OUTPUT QUALITY STANDARDS (applies to ALL generated code):

### Product Quality Bar:
- Output must be production-grade and portfolio-quality, not demo-grade
- Prioritize coherence: typography, spacing, color, and interaction language must feel unified
- Prefer fewer, better-crafted sections over many shallow sections
- Every screen should communicate clear purpose and hierarchy at first glance

### Visual Design:
- NEVER generate generic/template-looking output
- Use sophisticated color palettes — not default Tailwind colors
- Dark mode by default: slate-950/slate-900 backgrounds, light text
- Add subtle gradients: bg-gradient-to-br from-slate-950 via-indigo-950/30 to-slate-950
- Glass surfaces: backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl
- Colored shadows: shadow-xl shadow-indigo-500/10
- Smooth transitions on ALL interactive elements: transition-all duration-300
- Hover effects: hover:scale-[1.02] hover:shadow-2xl
- Professional typography: text-4xl font-bold tracking-tight for headings

### Tailwind CSS v4 Compatibility (CRITICAL):
- Use @import "tailwindcss"; — NOT @tailwind base/components/utilities
- Use @theme { } for custom design tokens instead of tailwind.config
- Use @utility for custom utility classes
- Only @apply standard Tailwind classes — never custom/non-existent ones
- Do NOT generate tailwind.config.ts or tailwind.config.js files
- Do NOT generate postcss.config.js — @tailwindcss/vite handles it

### Content:
- NEVER use placeholder text like "Lorem ipsum" or "Company Name"
- Generate REALISTIC, contextual content that matches the app's purpose
- Use real-sounding names, descriptions, and data
- Include at least 4-6 sample items in any list/grid (not just 2-3)
- Add micro-copy: button labels, empty states, tooltips, success messages

### Code Quality:
- Clean, well-structured code with clear component separation
- Proper error handling (loading states, error states, empty states)
- Responsive design — test at mobile (375px), tablet (768px), desktop (1280px)
- Accessible: proper labels, focus-visible states, color contrast
- Keyboard navigation and semantic landmarks by default
- No console errors
"""
