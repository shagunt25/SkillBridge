// ─── Mock Roadmap ─────────────────────────────────────────────────────────────
export const MOCK_ROADMAP = {
  match_score: 42,
  missing_skills: [
    'Docker', 'Kubernetes', 'AWS Lambda', 'PostgreSQL',
    'Redis', 'CI/CD Pipelines', 'GraphQL', 'System Design',
  ],
  learning_modules: [
    {
      title: 'Python & Programming Fundamentals',
      tasks: [
        { task_id: 'task-001', title: 'Master Python data types and control flow', is_completed: true },
        { task_id: 'task-002', title: 'Write OOP code with classes & inheritance', is_completed: true },
        { task_id: 'task-003', title: 'Handle exceptions, file I/O, and modules', is_completed: false },
        { task_id: 'task-004', title: 'Complete 10 LeetCode Easy problems in Python', is_completed: false },
      ],
      resource_search_terms: ['python beginner tutorial', 'python OOP course', 'python exercises'],
    },
    {
      title: 'SQL & Databases',
      tasks: [
        { task_id: 'task-005', title: 'Write SELECT, JOIN, GROUP BY, and subqueries', is_completed: false },
        { task_id: 'task-006', title: 'Design normalized schemas (1NF–3NF)', is_completed: false },
        { task_id: 'task-007', title: 'Understand indexes and query optimization', is_completed: false },
        { task_id: 'task-008', title: 'Build a small project using PostgreSQL', is_completed: false },
      ],
      resource_search_terms: ['sql for data analysts', 'postgresql tutorial', 'database design course'],
    },
    {
      title: 'REST APIs & Backend Basics',
      tasks: [
        { task_id: 'task-009', title: 'Understand HTTP methods, status codes, and headers', is_completed: false },
        { task_id: 'task-010', title: 'Build a CRUD REST API with FastAPI', is_completed: false },
        { task_id: 'task-011', title: 'Add JWT authentication and authorization', is_completed: false },
        { task_id: 'task-012', title: 'Write API docs with Swagger/OpenAPI', is_completed: false },
      ],
      resource_search_terms: ['fastapi tutorial', 'rest api design', 'jwt authentication guide'],
    },
    {
      title: 'Cloud & DevOps Fundamentals',
      tasks: [
        { task_id: 'task-013', title: 'Understand core AWS services (EC2, S3, Lambda)', is_completed: false },
        { task_id: 'task-014', title: 'Containerize an application with Docker', is_completed: false },
        { task_id: 'task-015', title: 'Set up a CI/CD pipeline with GitHub Actions', is_completed: false },
        { task_id: 'task-016', title: 'Deploy a simple app to a cloud platform', is_completed: false },
      ],
      resource_search_terms: ['aws cloud practitioner', 'docker getting started', 'github actions tutorial'],
    },
    {
      title: 'System Design',
      tasks: [
        { task_id: 'task-017', title: 'Study CAP theorem and distributed systems basics', is_completed: false },
        { task_id: 'task-018', title: 'Design a URL shortener and rate limiter', is_completed: false },
        { task_id: 'task-019', title: 'Understand caching, load balancing, and queues', is_completed: false },
        { task_id: 'task-020', title: 'Mock a system design interview for the target role', is_completed: false },
      ],
      resource_search_terms: ['system design primer', 'designing data-intensive applications'],
    },
  ],
};

// ─── Mock User ────────────────────────────────────────────────────────────────
export const MOCK_USER = {
  name: 'Alex Chen',
  email: 'alex.chen@example.com',
  targetRole: 'Backend Engineer',
  joinDate: 'January 2024',
};

// ─── Dashboard Stats ─────────────────────────────────────────────────────────
export const MOCK_STATS = {
  overallProgress: 10,   // percent
  tasksCompleted: 2,
  tasksTotal: 20,
  streak: 5,             // days
  modulesCompleted: 0,
};

// ─── Suggested Skills (for onboarding) ───────────────────────────────────────
export const SUGGESTED_SKILLS = [
  'Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Git',
  'TypeScript', 'REST APIs', 'HTML/CSS', 'Java', 'MongoDB', 'Linux',
];
