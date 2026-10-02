// ─── Mock Roadmap Matching Screenshot 1 & 5 ──────────────────────────────
export const MOCK_ROADMAP = {
  match_score: 50,
  missing_skills: [
    'FastAPI',
    'Docker',
    'CI/CD',
    'Kubernetes',
    'PyTorch',
    'Model Deployment',
    'Redis',
    'System Design',
  ],
  learning_modules: [
    {
      title: 'Phase 1: FastAPI & Docker Foundations',
      description: 'Build and containerize production-grade Python APIs.',
      estimated_hours: '23h',
      tasks: [
        { task_id: 'task-001', title: 'Build a REST API with FastAPI & Pydantic', is_completed: false, hours: '8h' },
        { task_id: 'task-002', title: 'Add async endpoints and dependency injection', is_completed: false, hours: '6h' },
        { task_id: 'task-003', title: 'Write a multi-stage Dockerfile for the service', is_completed: false, hours: '4h' },
        { task_id: 'task-004', title: 'Run the stack locally with Docker Compose', is_completed: false, hours: '5h' },
      ],
      resource_search_terms: ['fastapi tutorial', 'docker python microservice', 'docker compose fastapi'],
    },
    {
      title: 'Phase 2: CI/CD & Deployment',
      description: 'Automate testing and ship to the cloud with confidence.',
      estimated_hours: '20h',
      tasks: [
        { task_id: 'task-005', title: 'Configure GitHub Actions for pytest & ruff linting', is_completed: false, hours: '5h' },
        { task_id: 'task-006', title: 'Set up multi-stage image caching & container registry', is_completed: false, hours: '5h' },
        { task_id: 'task-007', title: 'Write infrastructure as code for ECS/App Runner', is_completed: false, hours: '6h' },
        { task_id: 'task-008', title: 'Configure automated release rollback & health checks', is_completed: false, hours: '4h' },
      ],
      resource_search_terms: ['github actions docker ci/cd', 'container deployment cloud', 'automated testing pipeline'],
    },
    {
      title: 'Phase 3: ML Model Serving',
      description: 'Serve PyTorch models behind low-latency inference APIs.',
      estimated_hours: '27h',
      tasks: [
        { task_id: 'task-009', title: 'Export trained PyTorch checkpoints to TorchScript/ONNX', is_completed: false, hours: '7h' },
        { task_id: 'task-010', title: 'Implement async batch inference worker pipeline', is_completed: false, hours: '6h' },
        { task_id: 'task-011', title: 'Configure Redis cache for precomputed embeddings', is_completed: false, hours: '6h' },
        { task_id: 'task-012', title: 'Measure p99 latency and profile memory usage with GPU', is_completed: false, hours: '8h' },
      ],
      resource_search_terms: ['pytorch model serving fastapi', 'onnx runtime inference python', 'redis cache embeddings'],
    },
    {
      title: 'Phase 4: Scale & System Design',
      description: 'Design for reliability, throughput, and Kubernetes.',
      estimated_hours: '28h',
      tasks: [
        { task_id: 'task-013', title: 'Design partitioned queues with Kafka/RabbitMQ for ingest', is_completed: false, hours: '8h' },
        { task_id: 'task-014', title: 'Write Kubernetes deployment manifests and ingress controllers', is_completed: false, hours: '8h' },
        { task_id: 'task-015', title: 'Configure horizontal pod autoscaling based on queue lag', is_completed: false, hours: '6h' },
        { task_id: 'task-016', title: 'Set up OpenTelemetry distributed tracing and Grafana dashboards', is_completed: false, hours: '6h' },
      ],
      resource_search_terms: ['kubernetes microservices deployment', 'system design distributed queue', 'opentelemetry python'],
    },
  ],
};

// ─── Mock User ────────────────────────────────────────────────────────────────
export const MOCK_USER = {
  name: 'Alex Chen',
  email: 'alex.chen@example.com',
  targetRole: 'Backend AI/ML Engineer',
  joinDate: 'January 2024',
};

// ─── Dashboard Stats ─────────────────────────────────────────────────────────
export const MOCK_STATS = {
  overallProgress: 0,
  tasksCompleted: 0,
  tasksTotal: 16,
  streak: 5,
  modulesCompleted: 0,
};

// ─── Suggested Skills (for onboarding) ───────────────────────────────────────
export const SUGGESTED_SKILLS = [
  'Python',
  'Git',
  'REST APIs',
  'Pandas',
  'PostgreSQL',
  'Linux',
  'Data Analysis',
  'FastAPI',
  'Docker',
  'Kubernetes',
  'Redis',
  'PyTorch',
];
