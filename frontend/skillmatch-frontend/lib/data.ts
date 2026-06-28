import { Job, CandidateProfile, SkillGap, Feature, Step } from "@/lib/types";

export const jobs: Job[] = [
  {
    id: "1",
    title: "Junior Machine Learning Engineer",
    company: "Fusemachines",
    location: "Kathmandu (Hybrid)",
    type: "Full-time",
    salary: "NPR 60k – 90k / month",
    postedAt: "2 days ago",
    matchScore: 92,
    skills: ["Python", "TensorFlow", "scikit-learn", "NLP", "Pandas"],
    description:
      "Work on real-world ML pipelines, from data preprocessing to model deployment, alongside a senior research team.",
    featured: true,
  },
  {
    id: "2",
    title: "Frontend Developer (React)",
    company: "Leapfrog Technology",
    location: "Lalitpur (On-site)",
    type: "Full-time",
    salary: "NPR 50k – 80k / month",
    postedAt: "1 day ago",
    matchScore: 86,
    skills: ["React", "TypeScript", "Next.js", "Tailwind CSS", "REST APIs"],
    description:
      "Build responsive, accessible interfaces for international clients using a modern React and TypeScript stack.",
    featured: true,
  },
  {
    id: "3",
    title: "Data Analyst Intern",
    company: "Khalti Digital Wallet",
    location: "Kathmandu (On-site)",
    type: "Internship",
    salary: "NPR 20k / month",
    postedAt: "4 days ago",
    matchScore: 78,
    skills: ["SQL", "Python", "Excel", "Data Visualization"],
    description:
      "Support the analytics team with reporting, dashboards, and exploratory analysis of payment data.",
  },
  {
    id: "4",
    title: "Backend Engineer (Django)",
    company: "Cedar Gate Technologies",
    location: "Kathmandu (Hybrid)",
    type: "Full-time",
    salary: "NPR 70k – 110k / month",
    postedAt: "5 days ago",
    matchScore: 81,
    skills: ["Python", "Django", "PostgreSQL", "Docker", "REST APIs"],
    description:
      "Design and maintain scalable backend services and APIs powering healthcare data products.",
  },
  {
    id: "5",
    title: "Junior NLP Engineer",
    company: "Docsumo",
    location: "Remote (Nepal)",
    type: "Full-time",
    salary: "NPR 65k – 95k / month",
    postedAt: "1 week ago",
    matchScore: 74,
    skills: ["Python", "spaCy", "Transformers", "NER", "PyTorch"],
    description:
      "Improve document-understanding models that extract structured data from unstructured documents.",
  },
  {
    id: "6",
    title: "QA / Automation Engineer",
    company: "Verisk Nepal",
    location: "Lalitpur (On-site)",
    type: "Contract",
    salary: "NPR 45k – 70k / month",
    postedAt: "1 week ago",
    matchScore: 69,
    skills: ["Selenium", "Python", "Jest", "CI/CD"],
    description:
      "Own test automation for web applications and integrate quality checks into the delivery pipeline.",
  },
];

export const profile: CandidateProfile = {
  name: "Aarav Sharma",
  title: "IT Graduate · Aspiring ML Engineer",
  location: "Kathmandu, Nepal",
  resumeScore: 84,
  topSkills: ["Python", "TensorFlow", "NLP", "scikit-learn", "SQL"],
  appliedCount: 7,
  matchedCount: 23,
  profileViews: 48,
};

export const skillGaps: SkillGap[] = [
  { skill: "Python", status: "have" },
  { skill: "TensorFlow", status: "have" },
  { skill: "NLP", status: "have" },
  { skill: "scikit-learn", status: "have" },
  { skill: "Docker", status: "missing" },
  { skill: "PyTorch", status: "missing" },
  { skill: "Cloud (AWS)", status: "missing" },
];

export const features: Feature[] = [
  {
    title: "Semantic Skill Matching",
    description:
      "Goes beyond keywords. We understand that a TensorFlow project means you know deep learning, even if the word isn't on your resume.",
    icon: "BrainCircuit",
  },
  {
    title: "Smart Resume Parsing",
    description:
      "Upload your PDF or Word resume and we automatically extract your skills, education, and experience in seconds.",
    icon: "FileSearch",
  },
  {
    title: "Local-First Matching",
    description:
      "Tuned for the Nepali IT market and local terminology, so recommendations actually reflect real opportunities here.",
    icon: "MapPin",
  },
  {
    title: "Skill Gap Insights",
    description:
      "See exactly which skills stand between you and your target role, so you know what to learn next.",
    icon: "Target",
  },
  {
    title: "Fair & Transparent",
    description:
      "Matches are based on skills, not background. Every recommendation can be explained and audited.",
    icon: "ShieldCheck",
  },
  {
    title: "Built for Employers Too",
    description:
      "Post a job and instantly see a ranked shortlist of qualified candidates, cutting manual screening time.",
    icon: "Building2",
  },
];

export const steps: Step[] = [
  {
    step: 1,
    title: "Upload your resume",
    description: "Drop in a PDF or Word file. We parse it and build your skill profile automatically.",
  },
  {
    step: 2,
    title: "We match your skills",
    description: "Our ML engine compares your profile against live job postings using semantic similarity.",
  },
  {
    step: 3,
    title: "Apply with confidence",
    description: "Browse ranked matches with a clear fit score and apply to roles that truly suit you.",
  },
];

export const stats = [
  { value: "12,000+", label: "IT graduates each year in Nepal" },
  { value: "92%", label: "Top match accuracy in testing" },
  { value: "3x", label: "Faster screening for employers" },
  { value: "500+", label: "Local IT roles tracked" },
];
