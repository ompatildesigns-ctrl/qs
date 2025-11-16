# Professional SaaS Landing Page Design System
## Bottleneck Analysis Platform - Investor Demo Quality

---

## GRADIENT RESTRICTION RULE

**NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.**

**PROHIBITED GRADIENTS:**
- blue-500 to purple-600
- purple-500 to pink-500
- green-500 to blue-500
- red to pink
- Any dark gradient combinations

**ENFORCEMENT RULE:**
IF gradient area exceeds 20% of viewport OR impacts readability
THEN fallback to solid colors or simple, two-color light gradients.

**ALLOWED GRADIENT USAGE:**
- Hero section background only (light to lighter gradients)
- Large CTA buttons (subtle, light gradients only)
- Decorative accent elements (max 10% of viewport)
- Section dividers and subtle overlays

---

## Design Personality & Brand Attributes

**Core Attributes:**
- **Sophisticated**: Professional, enterprise-grade quality
- **Trustworthy**: Financial data requires confidence and security
- **Authoritative**: CEO-level decision-making tool
- **Modern**: Clean, contemporary, not template-y
- **Data-Driven**: Visualization-first approach

**Visual Tone:**
- Clean minimalism with purposeful whitespace
- Bold typography for impact
- Professional color palette (no playful colors)
- Subtle animations that enhance, not distract
- Executive-level polish throughout

---

## Color System

### Primary Palette

```json
{
  "primary": {
    "50": "#f0f9ff",
    "100": "#e0f2fe",
    "200": "#bae6fd",
    "300": "#7dd3fc",
    "400": "#38bdf8",
    "500": "#0ea5e9",
    "600": "#0284c7",
    "700": "#0369a1",
    "800": "#075985",
    "900": "#0c4a6e"
  },
  "neutral": {
    "50": "#fafafa",
    "100": "#f5f5f5",
    "200": "#e5e5e5",
    "300": "#d4d4d4",
    "400": "#a3a3a3",
    "500": "#737373",
    "600": "#525252",
    "700": "#404040",
    "800": "#262626",
    "900": "#171717"
  },
  "accent": {
    "emerald": "#10b981",
    "amber": "#f59e0b",
    "rose": "#f43f5e"
  }
}
```

### Semantic Colors

```json
{
  "background": {
    "primary": "#ffffff",
    "secondary": "#fafafa",
    "tertiary": "#f5f5f5"
  },
  "text": {
    "primary": "#171717",
    "secondary": "#525252",
    "tertiary": "#737373",
    "inverse": "#ffffff"
  },
  "border": {
    "light": "#e5e5e5",
    "medium": "#d4d4d4",
    "dark": "#a3a3a3"
  },
  "success": "#10b981",
  "warning": "#f59e0b",
  "error": "#f43f5e",
  "info": "#0ea5e9"
}
```

### Gradient Definitions (Use Sparingly)

```css
/* Hero Section Only - Light Gradient */
.hero-gradient {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 50%, #fafafa 100%);
}

/* CTA Button - Subtle Gradient */
.cta-gradient {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
}

/* Accent Overlay - Decorative Only */
.accent-overlay {
  background: linear-gradient(90deg, rgba(14, 165, 233, 0.05) 0%, rgba(255, 255, 255, 0) 100%);
}
```

### Color Usage Priority

1. **White backgrounds (#ffffff)** for all cards, content areas, and main sections
2. **Light neutral backgrounds (#fafafa, #f5f5f5)** for alternating sections
3. **Primary blue (#0ea5e9)** for CTAs, links, and key interactive elements
4. **Neutral grays** for text hierarchy and borders
5. **Gradients** ONLY for hero section background (max 20% viewport)

---

## Typography System

### Font Families

```css
/* Primary Font - Headings & Display */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Secondary Font - Body & UI */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Monospace - Data & Metrics */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');
```

**Font Stack:**
```css
--font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'IBM Plex Mono', 'Courier New', monospace;
```

### Type Scale

```json
{
  "hero": {
    "mobile": "text-4xl (36px)",
    "tablet": "text-5xl (48px)",
    "desktop": "text-6xl (60px)",
    "lineHeight": "1.1",
    "fontWeight": "700",
    "letterSpacing": "-0.02em"
  },
  "h1": {
    "mobile": "text-3xl (30px)",
    "tablet": "text-4xl (36px)",
    "desktop": "text-5xl (48px)",
    "lineHeight": "1.2",
    "fontWeight": "700",
    "letterSpacing": "-0.01em"
  },
  "h2": {
    "mobile": "text-2xl (24px)",
    "tablet": "text-3xl (30px)",
    "desktop": "text-4xl (36px)",
    "lineHeight": "1.3",
    "fontWeight": "600",
    "letterSpacing": "-0.01em"
  },
  "h3": {
    "mobile": "text-xl (20px)",
    "tablet": "text-2xl (24px)",
    "desktop": "text-3xl (30px)",
    "lineHeight": "1.4",
    "fontWeight": "600"
  },
  "body-large": {
    "mobile": "text-lg (18px)",
    "tablet": "text-xl (20px)",
    "desktop": "text-xl (20px)",
    "lineHeight": "1.6",
    "fontWeight": "400"
  },
  "body": {
    "mobile": "text-base (16px)",
    "tablet": "text-base (16px)",
    "desktop": "text-lg (18px)",
    "lineHeight": "1.6",
    "fontWeight": "400"
  },
  "body-small": {
    "size": "text-sm (14px)",
    "lineHeight": "1.5",
    "fontWeight": "400"
  },
  "caption": {
    "size": "text-xs (12px)",
    "lineHeight": "1.4",
    "fontWeight": "500"
  },
  "metric": {
    "mobile": "text-3xl (30px)",
    "desktop": "text-5xl (48px)",
    "lineHeight": "1",
    "fontWeight": "700",
    "fontFamily": "IBM Plex Mono"
  }
}
```

### Typography Usage Rules

- **Hero Headlines**: Space Grotesk, 700 weight, tight letter-spacing (-0.02em)
- **Section Headlines**: Space Grotesk, 600-700 weight
- **Body Text**: Inter, 400 weight, generous line-height (1.6)
- **Metrics/Data**: IBM Plex Mono for financial figures and statistics
- **CTAs**: Inter, 600 weight, uppercase with letter-spacing (0.05em)

---

## Spacing System

### Base Unit: 4px

```json
{
  "spacing": {
    "0": "0px",
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
    "16": "64px",
    "20": "80px",
    "24": "96px",
    "32": "128px",
    "40": "160px",
    "48": "192px",
    "64": "256px"
  }
}
```

### Section Spacing

```css
/* Mobile */
.section-spacing-mobile {
  padding-top: 64px;
  padding-bottom: 64px;
}

/* Tablet */
.section-spacing-tablet {
  padding-top: 96px;
  padding-bottom: 96px;
}

/* Desktop */
.section-spacing-desktop {
  padding-top: 128px;
  padding-bottom: 128px;
}
```

### Container Widths

```css
.container-sm { max-width: 640px; }
.container-md { max-width: 768px; }
.container-lg { max-width: 1024px; }
.container-xl { max-width: 1280px; }
.container-2xl { max-width: 1536px; }
```

---

## Component Library

### Shadcn Components to Use

```json
{
  "navigation": {
    "component": "navigation-menu.jsx",
    "path": "/app/frontend/src/components/ui/navigation-menu.jsx",
    "usage": "Main navigation bar with dropdown menus"
  },
  "buttons": {
    "component": "button.jsx",
    "path": "/app/frontend/src/components/ui/button.jsx",
    "variants": ["default", "outline", "ghost", "link"],
    "sizes": ["sm", "default", "lg"]
  },
  "cards": {
    "component": "card.jsx",
    "path": "/app/frontend/src/components/ui/card.jsx",
    "usage": "Feature cards, testimonial cards, pricing cards"
  },
  "badges": {
    "component": "badge.jsx",
    "path": "/app/frontend/src/components/ui/badge.jsx",
    "usage": "Status indicators, labels, tags"
  },
  "separator": {
    "component": "separator.jsx",
    "path": "/app/frontend/src/components/ui/separator.jsx",
    "usage": "Section dividers"
  },
  "avatar": {
    "component": "avatar.jsx",
    "path": "/app/frontend/src/components/ui/avatar.jsx",
    "usage": "Testimonial avatars, team member photos"
  },
  "tabs": {
    "component": "tabs.jsx",
    "path": "/app/frontend/src/components/ui/tabs.jsx",
    "usage": "Feature showcase, product comparison"
  },
  "accordion": {
    "component": "accordion.jsx",
    "path": "/app/frontend/src/components/ui/accordion.jsx",
    "usage": "FAQ section"
  },
  "dialog": {
    "component": "dialog.jsx",
    "path": "/app/frontend/src/components/ui/dialog.jsx",
    "usage": "Demo request modal, video player"
  }
}
```

### Button Styles

```css
/* Primary CTA - Pill Shape */
.btn-primary {
  border-radius: 9999px; /* Full pill */
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
}

.btn-primary:active {
  transform: translateY(0);
}

/* Secondary CTA - Outline */
.btn-secondary {
  border-radius: 9999px;
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  border: 2px solid #0ea5e9;
  color: #0ea5e9;
  background: transparent;
  transition: background 0.2s ease, color 0.2s ease;
}

.btn-secondary:hover {
  background: #f0f9ff;
  color: #0284c7;
}

/* Ghost Button */
.btn-ghost {
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #525252;
  background: transparent;
  transition: background 0.2s ease;
}

.btn-ghost:hover {
  background: #f5f5f5;
  color: #171717;
}
```

### Card Styles

```css
/* Feature Card */
.feature-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 32px;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: #0ea5e9;
}

/* Testimonial Card */
.testimonial-card {
  background: #fafafa;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 24px;
}

/* Stat Card */
.stat-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}
```

---

## Layout System

### Grid Structure

```css
/* 12-Column Grid */
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 24px;
}

/* Responsive Grid */
.grid-responsive {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

/* Feature Grid - 3 Columns */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 32px;
}

@media (min-width: 768px) {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .feature-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### Landing Page Structure

```
1. Navigation Bar (sticky)
2. Hero Section (full viewport height)
3. Social Proof / Logo Bar
4. Problem Statement Section
5. Product Showcase (with screenshots)
6. Key Features Grid (3 columns)
7. Visual Bottleneck Flow Demo
8. Metrics & ROI Section
9. Testimonials
10. Pricing / CTA Section
11. FAQ
12. Footer
```

---

## Image Assets

### Hero Section Images

```json
{
  "hero_background": {
    "url": "Use light gradient background (no image)",
    "description": "Clean gradient from #f0f9ff to #ffffff"
  },
  "hero_product_screenshot": {
    "description": "Main dashboard screenshot showing bottleneck flow visualization",
    "placement": "Right side of hero, 50% width on desktop",
    "style": "Drop shadow, rounded corners (16px), slight tilt (2deg)"
  }
}
```

### Team/Testimonial Images

```json
{
  "testimonial_1": {
    "url": "https://images.unsplash.com/photo-1738750908048-14200459c3c9",
    "description": "Professional executive portrait - confident male",
    "usage": "CEO testimonial"
  },
  "testimonial_2": {
    "url": "https://images.unsplash.com/photo-1752118464988-2914fb27d0f0",
    "description": "Business leader with laptop",
    "usage": "VP Engineering testimonial"
  },
  "testimonial_3": {
    "url": "https://images.unsplash.com/photo-1752118465028-4a135f89e474",
    "description": "Confident business professional",
    "usage": "Product Manager testimonial"
  }
}
```

### Team Collaboration Images

```json
{
  "team_1": {
    "url": "https://images.unsplash.com/photo-1760611656007-f767a8082758",
    "description": "Two people working at office table",
    "usage": "Collaboration section background"
  },
  "team_2": {
    "url": "https://images.unsplash.com/photo-1759884247142-028abd1e8ac2",
    "description": "Woman working at desk through glass",
    "usage": "About section or team showcase"
  },
  "team_3": {
    "url": "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg",
    "description": "Professional handshake collaboration",
    "usage": "Partnership or trust section"
  }
}
```

### Data Visualization Images

```json
{
  "network_viz_1": {
    "url": "https://images.unsplash.com/photo-1664526937033-fe2c11f1be25",
    "description": "Abstract network diagram with nodes",
    "usage": "Bottleneck flow section background or accent"
  },
  "network_viz_2": {
    "url": "https://images.unsplash.com/photo-1664854953181-b12e6dda8b7c",
    "description": "Tree structure with connections",
    "usage": "Feature showcase background"
  },
  "network_viz_3": {
    "url": "https://images.unsplash.com/photo-1738082956220-a1f20a8632ce",
    "description": "3D cluster of connected spheres",
    "usage": "Hero section accent or decorative element"
  },
  "network_viz_4": {
    "url": "https://images.unsplash.com/photo-1664526936810-ec0856d31b92",
    "description": "Network diagram visualization",
    "usage": "Technology section or product features"
  }
}
```

---

## Motion & Animations

### Animation Principles

- **Subtle and purposeful**: Animations should enhance, not distract
- **Performance-first**: Use CSS transforms and opacity for smooth 60fps
- **Consistent timing**: Use standard easing functions
- **Respect reduced motion**: Always include prefers-reduced-motion queries

### Framer Motion Integration

```bash
# Already installed in package.json
npm install framer-motion
```

### Animation Patterns

```javascript
// Fade In Up
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: "easeOut" }
};

// Stagger Children
const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

// Scale on Hover
const scaleOnHover = {
  whileHover: { scale: 1.05 },
  transition: { duration: 0.2 }
};

// Slide In From Left
const slideInLeft = {
  initial: { opacity: 0, x: -50 },
  animate: { opacity: 1, x: 0 },
  transition: { duration: 0.6, ease: "easeOut" }
};

// Parallax Scroll
const parallaxScroll = {
  initial: { y: 0 },
  animate: { y: -50 },
  transition: { duration: 1, ease: "linear" }
};
```

### Hover States

```css
/* Button Hover */
.interactive-element {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.interactive-element:hover {
  transform: translateY(-2px);
}

/* Card Hover */
.card-hover {
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

/* Link Hover */
.link-hover {
  position: relative;
  transition: color 0.2s ease;
}

.link-hover::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: #0ea5e9;
  transition: width 0.3s ease;
}

.link-hover:hover::after {
  width: 100%;
}
```

### Scroll Animations

```javascript
// Use Framer Motion's useScroll and useTransform
import { useScroll, useTransform, motion } from 'framer-motion';

const ScrollAnimation = () => {
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.8]);
  
  return (
    <motion.div style={{ opacity, scale }}>
      {/* Content */}
    </motion.div>
  );
};
```

---

## Accessibility Guidelines

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text on white: Minimum 4.5:1 ratio
- Large text (18px+): Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio

**Keyboard Navigation:**
- All interactive elements must be keyboard accessible
- Visible focus states required
- Logical tab order

**Screen Reader Support:**
- Semantic HTML elements
- ARIA labels where needed
- Alt text for all images

### Focus States

```css
/* Focus Visible */
*:focus-visible {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
  border-radius: 4px;
}

/* Button Focus */
.btn:focus-visible {
  outline: 2px solid #0ea5e9;
  outline-offset: 4px;
}

/* Link Focus */
a:focus-visible {
  outline: 2px solid #0ea5e9;
  outline-offset: 2px;
  border-radius: 2px;
}
```

### Data-TestID Requirements

**All interactive elements MUST include data-testid attributes:**

```javascript
// Navigation
<nav data-testid="main-navigation">
  <button data-testid="nav-cta-button">Get Started</button>
</nav>

// Hero Section
<section data-testid="hero-section">
  <h1 data-testid="hero-headline">Find Your Bottlenecks</h1>
  <button data-testid="hero-primary-cta">Book Demo</button>
  <button data-testid="hero-secondary-cta">Watch Video</button>
</section>

// Feature Cards
<div data-testid="feature-card-1">
  <h3 data-testid="feature-title">Visual Bottleneck Flow</h3>
</div>

// Testimonials
<div data-testid="testimonial-card-1">
  <p data-testid="testimonial-quote">...</p>
  <span data-testid="testimonial-author">John Doe</span>
</div>

// Forms
<form data-testid="demo-request-form">
  <input data-testid="form-input-email" />
  <button data-testid="form-submit-button">Submit</button>
</form>

// Metrics
<div data-testid="metric-cost-of-delay">$15.4M</div>
<div data-testid="metric-team-roi">1,015%</div>
```

---

## Additional Libraries & Integrations

### Recharts for Data Visualization

```bash
npm install recharts
```

**Usage:**
- ROI charts
- Velocity trend graphs
- Cost of delay visualizations

**Example:**
```javascript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const VelocityChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
      <XAxis dataKey="month" stroke="#737373" />
      <YAxis stroke="#737373" />
      <Tooltip />
      <Line type="monotone" dataKey="velocity" stroke="#0ea5e9" strokeWidth={3} />
    </LineChart>
  </ResponsiveContainer>
);
```

### React Icons (Lucide React)

```bash
# Already installed
npm install lucide-react
```

**Icon Usage:**
```javascript
import { ArrowRight, CheckCircle, TrendingUp, Users, DollarSign } from 'lucide-react';

// Use in CTAs
<button>
  Get Started <ArrowRight className="ml-2" />
</button>

// Use in feature cards
<CheckCircle className="w-6 h-6 text-emerald-500" />
```

### Intersection Observer for Scroll Animations

```javascript
import { useEffect, useRef, useState } from 'react';

const useInView = (options) => {
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsInView(entry.isIntersecting);
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [options]);

  return [ref, isInView];
};
```

---

## Landing Page Sections - Detailed Specifications

### 1. Navigation Bar

**Structure:**
- Logo (left)
- Navigation links (center): Features, Pricing, About, Resources
- CTA button (right): "Book Demo"

**Styling:**
```css
.navbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #e5e5e5;
  padding: 16px 0;
}
```

**Component:** Use `navigation-menu.jsx` from shadcn

### 2. Hero Section

**Layout:**
- Left: Headline + Subheadline + CTAs (50%)
- Right: Product screenshot (50%)

**Content:**
```
Headline: "Find the $15M Bottleneck Killing Your Velocity"
Subheadline: "Visual quantum analysis that shows exactly where your team is blocked—and who's carrying the burden."
Primary CTA: "Book Demo"
Secondary CTA: "Watch 2-Min Demo"
```

**Styling:**
```css
.hero-section {
  min-height: 90vh;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 50%, #fafafa 100%);
  padding: 80px 0;
}
```

### 3. Social Proof / Logo Bar

**Content:**
- "Trusted by leading engineering teams"
- 4-6 company logos (grayscale, hover to color)

**Styling:**
```css
.logo-bar {
  padding: 48px 0;
  background: #fafafa;
  border-top: 1px solid #e5e5e5;
  border-bottom: 1px solid #e5e5e5;
}

.logo-item {
  filter: grayscale(100%);
  opacity: 0.6;
  transition: filter 0.3s ease, opacity 0.3s ease;
}

.logo-item:hover {
  filter: grayscale(0%);
  opacity: 1;
}
```

### 4. Problem Statement Section

**Content:**
```
Headline: "Your Team is Blocked. But Where?"
Body: "Traditional project management tools show you tasks. We show you the invisible bottlenecks costing you millions."
```

**Layout:**
- Centered text (max-width: 768px)
- 3-column grid of pain points

**Pain Points:**
1. "ANUP is blocking $10M in work"
2. "Velocity dropped 85% last quarter"
3. "No visibility into team capacity"

### 5. Product Showcase

**Content:**
- Large product screenshot
- Annotated callouts highlighting key features
- Interactive demo or video

**Features to Highlight:**
1. Visual Quantum Bottleneck Flow (circular nodes)
2. People Bottleneck Analyzer
3. Intelligent Insights
4. Executive Time Filters

**Styling:**
```css
.product-showcase {
  padding: 128px 0;
  background: #ffffff;
}

.product-screenshot {
  border-radius: 16px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e5e5;
}
```

### 6. Key Features Grid

**Layout:** 3-column grid (1 column mobile, 2 tablet, 3 desktop)

**Features:**
1. **Visual Bottleneck Flow**
   - Icon: Network diagram
   - Description: "Circular node visualization with drill-down capabilities"

2. **People Analyzer**
   - Icon: Users
   - Description: "See who's blocked and their workload burden"

3. **Intelligent Insights**
   - Icon: TrendingUp
   - Description: "Velocity +15,810%, trend analysis, predictive alerts"

4. **Executive Filters**
   - Icon: Calendar
   - Description: "This Quarter, This Year, custom date ranges"

5. **Cost of Delay**
   - Icon: DollarSign
   - Description: "$15.4M impact visualization"

6. **Team ROI**
   - Icon: CheckCircle
   - Description: "1,015% team efficiency improvement"

**Component:** Use `card.jsx` from shadcn with hover effects

### 7. Visual Bottleneck Flow Demo

**Content:**
- Interactive or animated visualization
- Shows circular nodes with connections
- Drill-down interaction demo

**Implementation:**
- Use D3.js or React Flow for node visualization
- Animate on scroll into view
- Show before/after comparison

### 8. Metrics & ROI Section

**Layout:**
- Dark background (#171717) with light text
- 4-column grid of key metrics

**Metrics:**
1. "$15.4M" - Cost of Delay Identified
2. "1,015%" - Team ROI Improvement
3. "+15,810%" - Velocity Increase
4. "12 hours" - Data Lifecycle

**Styling:**
```css
.metrics-section {
  background: #171717;
  color: #ffffff;
  padding: 96px 0;
}

.metric-card {
  text-align: center;
}

.metric-value {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 48px;
  font-weight: 700;
  color: #0ea5e9;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 16px;
  color: #a3a3a3;
}
```

### 9. Testimonials

**Layout:**
- 3-column grid (1 mobile, 2 tablet, 3 desktop)
- Avatar + Quote + Name + Title

**Component:** Use `card.jsx` and `avatar.jsx` from shadcn

**Example Testimonial:**
```
Quote: "This tool found a $10M bottleneck we didn't even know existed. Game changer for our engineering org."
Name: "Sarah Chen"
Title: "VP Engineering, TechCorp"
Avatar: Use testimonial images from image assets
```

### 10. Pricing / CTA Section

**Content:**
```
Headline: "See Your Bottlenecks in 15 Minutes"
Subheadline: "Book a personalized demo and we'll analyze your team's data live."
Primary CTA: "Book Demo"
Secondary: "Start Free Trial"
```

**Styling:**
```css
.cta-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  padding: 96px 0;
  text-align: center;
}
```

### 11. FAQ

**Component:** Use `accordion.jsx` from shadcn

**Questions:**
1. "How does the bottleneck analysis work?"
2. "What data sources do you integrate with?"
3. "How long does setup take?"
4. "Is my data secure?"
5. "What's the pricing model?"

### 12. Footer

**Layout:**
- 4-column grid
- Logo + tagline (left)
- Product links
- Company links
- Legal links

**Styling:**
```css
.footer {
  background: #fafafa;
  border-top: 1px solid #e5e5e5;
  padding: 64px 0 32px;
}
```

---

## Responsive Breakpoints

```css
/* Mobile First */
.container {
  padding: 0 16px;
}

/* Tablet: 768px */
@media (min-width: 768px) {
  .container {
    padding: 0 32px;
  }
}

/* Desktop: 1024px */
@media (min-width: 1024px) {
  .container {
    padding: 0 48px;
  }
}

/* Large Desktop: 1280px */
@media (min-width: 1280px) {
  .container {
    max-width: 1280px;
    margin: 0 auto;
  }
}
```

---

## Performance Optimization

### Image Optimization
- Use WebP format with JPEG fallback
- Lazy load images below the fold
- Responsive images with srcset

### Code Splitting
```javascript
// Lazy load heavy components
const BottleneckFlow = lazy(() => import('./components/BottleneckFlow'));
const VideoPlayer = lazy(() => import('./components/VideoPlayer'));
```

### Font Loading
```css
/* Preload critical fonts */
<link rel="preload" href="/fonts/space-grotesk.woff2" as="font" type="font/woff2" crossorigin>
```

---

## Instructions to Main Agent

### Implementation Priority

1. **Phase 1: Foundation**
   - Set up color system in index.css
   - Import Google Fonts
   - Create base layout components
   - Implement navigation bar

2. **Phase 2: Hero & Core Sections**
   - Build hero section with gradient background
   - Add social proof logo bar
   - Create problem statement section
   - Implement product showcase with screenshots

3. **Phase 3: Features & Content**
   - Build feature grid with cards
   - Create metrics section
   - Add testimonials
   - Implement FAQ accordion

4. **Phase 4: Polish & Animations**
   - Add Framer Motion animations
   - Implement scroll effects
   - Add hover states
   - Test responsive behavior

5. **Phase 5: Testing & Optimization**
   - Add all data-testid attributes
   - Test keyboard navigation
   - Verify color contrast
   - Optimize images and performance

### Key Implementation Notes

**DO:**
- Use white backgrounds for all content cards
- Keep gradients to hero section only (max 20% viewport)
- Use Space Grotesk for headlines, Inter for body
- Add generous whitespace (2-3x more than feels comfortable)
- Include data-testid on all interactive elements
- Use shadcn components as primary UI library
- Implement subtle hover animations on all interactive elements
- Use IBM Plex Mono for all financial metrics
- Add parallax effects on scroll
- Use pill-shaped buttons for primary CTAs

**DON'T:**
- Use dark gradients (purple/pink/blue-purple)
- Apply gradients to text-heavy areas
- Use generic centered layouts
- Skip hover states
- Forget responsive breakpoints
- Use emoji icons (use Lucide React instead)
- Apply universal transitions (transition: all)
- Center-align the app container
- Use HTML-based components (use shadcn instead)

### Component File Structure

```
/app/frontend/src/
├── components/
│   ├── ui/ (shadcn components - already exists)
│   ├── landing/
│   │   ├── Navigation.js
│   │   ├── Hero.js
│   │   ├── SocialProof.js
│   │   ├── ProblemStatement.js
│   │   ├── ProductShowcase.js
│   │   ├── FeaturesGrid.js
│   │   ├── BottleneckFlowDemo.js
│   │   ├── MetricsSection.js
│   │   ├── Testimonials.js
│   │   ├── CTASection.js
│   │   ├── FAQ.js
│   │   └── Footer.js
├── App.js (main landing page)
├── App.css (component-specific styles)
└── index.css (global styles, design tokens)
```

### CSS Custom Properties Setup

Add to `/app/frontend/src/index.css`:

```css
@layer base {
  :root {
    /* Colors */
    --color-primary-50: 240 249 255;
    --color-primary-500: 14 165 233;
    --color-primary-600: 2 132 199;
    --color-neutral-50: 250 250 250;
    --color-neutral-900: 23 23 23;
    
    /* Typography */
    --font-display: 'Space Grotesk', -apple-system, sans-serif;
    --font-body: 'Inter', -apple-system, sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
    
    /* Spacing */
    --spacing-section-mobile: 64px;
    --spacing-section-tablet: 96px;
    --spacing-section-desktop: 128px;
    
    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
    --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.12);
    --shadow-xl: 0 24px 64px rgba(0, 0, 0, 0.16);
    
    /* Border Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-full: 9999px;
  }
}
```

---

## Common Mistakes to Avoid

### ❌ **Don't:**
- Mix multiple gradient directions in same section
- Use gradients on small UI elements
- Skip responsive font sizing
- Ignore glassmorphism effects for secondary buttons
- Forget hover and focus states
- Use dark purple, dark blue, dark pink, dark red, dark orange in any gradient
- Apply transition: all (breaks transforms)
- Center-align app container
- Use emoji icons

### ✅ **Do:**
- Keep gradients for hero sections and major CTAs only
- Use solid colors for content and reading areas
- Maintain consistent spacing using the spacing system
- Test on mobile devices with touch interactions
- Include accessibility features (focus states, contrast)
- Use the pill/capsule button style for primary actions
- Add data-testid to all interactive elements
- Use Lucide React for icons
- Implement subtle micro-animations
- Use generous whitespace

---

## Final Quality Checklist

Before considering the landing page complete, verify:

- [ ] All sections implemented per specifications
- [ ] Color contrast meets WCAG AA standards
- [ ] All interactive elements have hover states
- [ ] All interactive elements have data-testid attributes
- [ ] Responsive on mobile, tablet, desktop
- [ ] Fonts loaded correctly (Space Grotesk, Inter, IBM Plex Mono)
- [ ] Gradients limited to hero section (<20% viewport)
- [ ] All images optimized and lazy-loaded
- [ ] Framer Motion animations smooth and purposeful
- [ ] Keyboard navigation works throughout
- [ ] Focus states visible on all interactive elements
- [ ] No console errors or warnings
- [ ] Performance: Lighthouse score >90
- [ ] Accessibility: Lighthouse score >90

---

## Reference Quality Standards

**Inspiration Sources:**
- searchparty.com: Bold minimalist confidence, clean whitespace
- atlas.so: Professional white-glove service feel
- eng-metrics-dash.preview.emergentagent.com: Data visualization excellence

**Quality Bar:**
- Investor-ready polish
- CEO-level messaging
- Enterprise-grade professionalism
- No template-y feel
- Billion-dollar quality

---

# GENERAL UI/UX DESIGN GUIDELINES

## Universal Design Principles

### Transition Rules
- **NEVER** apply universal transitions like `transition: all` - this breaks transforms
- **ALWAYS** add transitions for specific properties: `transition-colors`, `transition-transform`, `transition-opacity`
- Example: `className="transition-colors duration-300"` NOT `className="transition-all"`

### Text Alignment
- **NEVER** center-align the app container (no `.App { text-align: center; }`)
- This disrupts natural reading flow
- Only center-align specific elements like headings or CTAs when appropriate

### Icon Usage
- **NEVER** use emoji characters for icons (🤖🧠💭💡🔮 etc.)
- **ALWAYS** use FontAwesome CDN or Lucide React library (already installed)
- Example: `import { TrendingUp } from 'lucide-react';`

### Gradient Restrictions (CRITICAL)
- **NEVER** use dark/saturated gradient combos (purple/pink, blue-500 to purple-600, etc.)
- **NEVER** let gradients cover more than 20% of viewport
- **NEVER** apply gradients to text-heavy content or reading areas
- **NEVER** use gradients on small UI elements (<100px width)
- **NEVER** stack multiple gradient layers in same viewport

**Enforcement:** If gradient area exceeds 20% of viewport OR affects readability, use solid colors

**Allowed gradient usage:**
- Section backgrounds (not content backgrounds)
- Hero section header content (light to lighter gradients)
- Decorative overlays and accent elements only
- Large CTA buttons with 2-3 mild colors

### Animation & Interaction
- Every interaction needs micro-animations
- Hover states, transitions, entrance animations are essential
- Static designs feel dead - add life through motion
- Use 2-3x more spacing than feels comfortable
- Cramped designs look cheap

### Texture & Details
- Add subtle grain textures or noise overlays
- Consider custom cursors for enhanced UX
- Style selection states
- Create thoughtful loading animations
- These details separate good from extraordinary

### Component Reuse
- Prioritize using pre-existing components from `src/components/ui`
- Create new components that match existing style and conventions
- Examine existing components to understand patterns before creating new ones

### Component Standards
- **IMPORTANT:** Do not use HTML-based components (dropdown, calendar, toast)
- **MUST** always use `/app/frontend/src/components/ui/` as primary components
- These are modern, stylish, and accessible

### Best Practices
- Use Shadcn/UI as primary component library for consistency and accessibility
- Import path: `./components/[component-name]`

### Export Conventions
- Components MUST use named exports: `export const ComponentName = ...`
- Pages MUST use default exports: `export default function PageName() {...}`

### Toast Notifications
- Use `sonner` for toasts
- Sonner component located in `/app/src/components/ui/sonner.jsx`

### Visual Depth
- Use 2-4 color gradients for depth
- Add subtle textures/noise overlays
- Use CSS-based noise to avoid flat visuals
- Avoid overuse - balance is key

### Responsive Design
- Mobile-first approach always
- Test on actual mobile devices
- Ensure touch targets are adequate (min 44x44px)
- Consider thumb zones for mobile navigation

### Accessibility (WCAG AA Minimum)
- Color contrast ratios: 4.5:1 for body text, 3:1 for large text
- All interactive elements need visible focus states
- Keyboard navigation must work throughout
- Include proper ARIA labels
- Test with screen readers

### Data-TestID Requirements
- All interactive elements MUST include `data-testid` attribute
- Use kebab-case convention
- Define element's role, not appearance
- Example: `data-testid="login-form-submit-button"`
- This creates stable interface for automated testing

---

**Remember:** The result should feel human-made, visually appealing, and easy for AI agents to implement. Focus on good contrast, balanced font sizes, proper gradients, sufficient whitespace, and thoughtful motion and hierarchy. Avoid overuse of elements and deliver a polished, effective design system.

---

**This design system is optimized for React .js files (not .tsx). All components should be created as .js files with proper PropTypes validation where needed.**
