export type JobType = "Full-time" | "Part-time" | "Internship" | "Contract";

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  type: JobType;
  salary: string;
  postedAt: string;
  matchScore: number; // 0-100
  skills: string[];
  description: string;
  featured?: boolean;
}

export interface SkillGap {
  skill: string;
  status: "have" | "missing";
}

export interface CandidateProfile {
  name: string;
  title: string;
  location: string;
  resumeScore: number;
  topSkills: string[];
  appliedCount: number;
  matchedCount: number;
  profileViews: number;
}

export interface Feature {
  title: string;
  description: string;
  icon: string; // lucide icon name
}

export interface Step {
  step: number;
  title: string;
  description: string;
}
