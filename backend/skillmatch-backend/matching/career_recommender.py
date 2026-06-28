"""Career Recommendation Engine.

Predicts the top-10 best-fit job roles for a candidate based on:
  • Technical skills (skill-to-role affinity matrix)
  • Degree / educational background
  • CGPA bracket
  • Certifications
  • Preferred role signal from profile

Each recommendation includes:
  - role name
  - confidence (0–1)
  - reason string
  - suggested learning path items

Usage
-----
    from matching.career_recommender import CareerRecommendationEngine
    recs = CareerRecommendationEngine().recommend(user)
    # recs = {"recommended_roles": [...], "learning_paths": [...], "top_role": "..."}
"""
from __future__ import annotations
import math
from collections import defaultdict

# ── Role → required skill clusters ────────────────────────────────────────────
ROLE_SKILL_MAP: dict[str, list[str]] = {
    "Backend Developer": [
        "Python","Django","FastAPI","Flask","Node.js","Express.js","PostgreSQL",
        "MySQL","MongoDB","REST APIs","Docker","Linux","Git","Redis",
    ],
    "Frontend Developer": [
        "React","Next.js","Vue.js","Angular","JavaScript","TypeScript","HTML",
        "CSS","Tailwind CSS","Redux","Bootstrap","Figma",
    ],
    "Full Stack Developer": [
        "React","Django","Node.js","PostgreSQL","MongoDB","Docker","REST APIs",
        "JavaScript","TypeScript","HTML","CSS","Git",
    ],
    "ML Engineer": [
        "Python","scikit-learn","TensorFlow","PyTorch","Pandas","NumPy",
        "Matplotlib","SQL","Docker","Keras","Hugging Face","MLflow",
    ],
    "Data Analyst": [
        "Python","SQL","Pandas","NumPy","Excel","Power BI","Tableau",
        "Matplotlib","PostgreSQL","Statistics",
    ],
    "Data Scientist": [
        "Python","R","scikit-learn","TensorFlow","Pandas","NumPy","SQL",
        "Matplotlib","Statistics","Spark","Tableau","Keras",
    ],
    "DevOps Engineer": [
        "Docker","Kubernetes","Linux","AWS","Azure","GitHub Actions","Jenkins",
        "Terraform","Ansible","Bash","CI/CD","Nginx","Python",
    ],
    "QA Engineer": [
        "Selenium","Pytest","JUnit","Postman","Jest","Cypress","Java","Python",
        "SQL","Jira","TestNG","Git",
    ],
    "Mobile App Developer": [
        "Flutter","React Native","Dart","Kotlin","Swift","Android SDK",
        "Firebase","REST APIs","Git","JavaScript",
    ],
    "Cloud Engineer": [
        "AWS","Azure","GCP","Docker","Kubernetes","Terraform","Linux",
        "Python","Bash","Networking","CI/CD",
    ],
    "Cybersecurity Analyst": [
        "Kali Linux","Wireshark","Metasploit","Burp Suite","Python","Nmap",
        "Penetration Testing","OWASP","Linux","Networking","SQL",
    ],
    "AI Engineer": [
        "Python","TensorFlow","PyTorch","Hugging Face","LangChain","OpenCV",
        "NLTK","spaCy","Docker","REST APIs","Kubernetes",
    ],
    "NLP Engineer": [
        "Python","NLTK","spaCy","Hugging Face","TensorFlow","PyTorch",
        "scikit-learn","Pandas","REST APIs","Docker",
    ],
    "Computer Vision Engineer": [
        "Python","OpenCV","TensorFlow","PyTorch","Keras","YOLO","NumPy",
        "scikit-learn","Docker","C++",
    ],
    "Business Analyst": [
        "Excel","SQL","Power BI","Tableau","Python","Jira","Figma",
        "Communication","Project Management","Data Analysis",
    ],
    "Product Analyst": [
        "SQL","Python","Excel","Tableau","Power BI","Jira","Figma",
        "Data Analysis","Communication","A/B Testing",
    ],
    "Blockchain Developer": [
        "Solidity","Web3.js","Ethereum","Smart Contracts","JavaScript","Python",
        "Node.js","PostgreSQL","Git","Hardhat",
    ],
    "Database Administrator": [
        "PostgreSQL","MySQL","Oracle","MS SQL","MongoDB","Redis","SQL",
        "Linux","Python","Backup & Recovery","Performance Tuning",
    ],
    "System Analyst": [
        "SQL","Python","Java","Linux","Networking","Jira","Documentation",
        "REST APIs","UML","Business Analysis",
    ],
    "Software Engineer": [
        "Python","Java","C++","JavaScript","SQL","Git","Linux","REST APIs",
        "Docker","Algorithms","Data Structures",
    ],
}

# ── Degree → role affinity boost ─────────────────────────────────────────────
DEGREE_ROLE_BOOST: dict[str, list[str]] = {
    "BSc CSIT":             ["Backend Developer","Full Stack Developer","Software Engineer"],
    "BE Computer Eng":      ["Software Engineer","Backend Developer","DevOps Engineer"],
    "BE Software Eng":      ["Software Engineer","Full Stack Developer","Cloud Engineer"],
    "BIT":                  ["Frontend Developer","Full Stack Developer","Mobile App Developer"],
    "BCA":                  ["Business Analyst","System Analyst","Database Administrator"],
    "BIM":                  ["Business Analyst","Product Analyst","System Analyst"],
    "BICTE":                ["QA Engineer","System Analyst","Database Administrator"],
    "BSc Data Science":     ["Data Scientist","Data Analyst","ML Engineer"],
    "BSc AI & ML":          ["AI Engineer","ML Engineer","NLP Engineer"],
    "BSc Cyber Security":   ["Cybersecurity Analyst","DevOps Engineer","Cloud Engineer"],
}

# ── Learning path suggestions for missing skills ──────────────────────────────
LEARNING_RESOURCES: dict[str, list[str]] = {
    "Docker":            ["Docker Official Docs","KodeKloud Docker Course","Play with Docker"],
    "Kubernetes":        ["Kubernetes.io Tutorials","CKAD Study Guide","KodeKloud K8s"],
    "AWS":               ["AWS Free Tier Labs","Cloud Quest (AWS)","A Cloud Guru"],
    "React":             ["React Official Docs","Full Stack Open","Scrimba React"],
    "Next.js":           ["Next.js Official Docs","Lee Robinson's Next.js Course"],
    "TensorFlow":        ["TensorFlow Tutorials","DeepLearning.AI Specialization"],
    "PyTorch":           ["PyTorch Tutorials","fast.ai Practical DL"],
    "PostgreSQL":        ["PostgreSQL Official Docs","Mode SQL Tutorial"],
    "Django":            ["Django Official Tutorial","DjangoGirls Tutorial","TestDriven.io"],
    "scikit-learn":      ["scikit-learn User Guide","Hands-On ML (Géron)"],
    "Selenium":          ["Selenium with Python","ISTQB CTFL Study Guide"],
    "Flutter":           ["Flutter Official Docs","Angela Yu Flutter Bootcamp"],
    "Solidity":          ["CryptoZombies","Alchemy University","Hardhat Docs"],
    "Terraform":         ["HashiCorp Learn","Terraform: Up & Running"],
    "spaCy":             ["spaCy Official Docs","Ines Montani's spaCy Course"],
    "Hugging Face":      ["HuggingFace Course","NLPF Transformers Docs"],
}


class CareerRecommendationEngine:

    def recommend(self, user) -> dict:
        """Return top-10 role recommendations with confidence and learning paths."""
        profile = getattr(user, "candidate_profile", None)
        cand_skills_lower = set()
        degree = ""
        cgpa = 0.0
        certs = []
        preferred = ""

        if profile:
            cand_skills_lower = {s.lower() for s in profile.skills_list()}
            degree = profile.degree or ""
            cgpa = float(profile.cgpa or 0.0)
            certs = [c.lower() for c in profile.certifications_list()]
            preferred = profile.preferred_role or ""

        # ── Score each role ───────────────────────────────────────────────
        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = defaultdict(list)

        for role, required_skills in ROLE_SKILL_MAP.items():
            req_lower = [s.lower() for s in required_skills]
            total     = len(req_lower)
            matched   = sum(1 for s in req_lower if s in cand_skills_lower)
            base_score = matched / total if total else 0.0

            # Degree boost
            if degree in DEGREE_ROLE_BOOST and role in DEGREE_ROLE_BOOST[degree]:
                base_score = min(1.0, base_score + 0.12)
                reasons[role].append(f"Degree ({degree}) aligns with this role")

            # Preferred role boost
            if preferred and preferred.lower() in role.lower():
                base_score = min(1.0, base_score + 0.08)
                reasons[role].append(f"Matches your preferred role preference")

            # CGPA boost
            if cgpa >= 3.7:
                base_score = min(1.0, base_score + 0.05)
            elif cgpa < 2.5 and base_score > 0:
                base_score *= 0.85

            # Cert boost
            cert_bonus = sum(0.03 for c in certs if any(kw in c for kw in ["aws","azure","gcp","docker","k8s","google","certified","scrum"]))
            base_score = min(1.0, base_score + cert_bonus)

            if matched > 0:
                reasons[role].append(f"{matched}/{total} required skills matched")
            scores[role] = base_score

        # Sort and take top 10
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

        # ── Build output ──────────────────────────────────────────────────
        recommended_roles = []
        for role, confidence in ranked:
            req_skills_lower = [s.lower() for s in ROLE_SKILL_MAP[role]]
            missing = [s for s in ROLE_SKILL_MAP[role] if s.lower() not in cand_skills_lower]

            reason_parts = reasons[role][:2] if reasons[role] else ["Based on your skill profile"]
            reason = "; ".join(reason_parts)

            recommended_roles.append({
                "role":           role,
                "confidence":     round(confidence, 3),
                "confidence_pct": int(round(confidence * 100)),
                "reason":         reason,
                "missing_skills": missing[:5],
            })

        # ── Learning paths ─────────────────────────────────────────────────
        all_missing: dict[str, int] = defaultdict(int)
        for item in recommended_roles[:3]:
            for skill in item["missing_skills"]:
                all_missing[skill] += 1

        learning_paths = []
        for skill, importance in sorted(all_missing.items(), key=lambda x: -x[1])[:8]:
            resources = LEARNING_RESOURCES.get(skill, ["Search for free tutorials on YouTube / Coursera"])
            priority = "high" if importance >= 2 else "medium"
            learning_paths.append({
                "skill":     skill,
                "priority":  priority,
                "resources": resources[:3],
                "reason":    f"Missing from your top-{importance+1} recommended roles",
            })

        top_role = recommended_roles[0]["role"] if recommended_roles else ""

        return {
            "recommended_roles": recommended_roles,
            "learning_paths":    learning_paths,
            "top_role":          top_role,
        }
