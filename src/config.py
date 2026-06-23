"""Project configuration for the Redrob candidate ranker."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CHALLENGE_DATA_DIR = (
    ROOT_DIR
    / "data"
    / "[PUB] India_runs_data_and_ai_challenge"
    / "India_runs_data_and_ai_challenge"
)

DEFAULT_CANDIDATES_PATH = CHALLENGE_DATA_DIR / "candidates.jsonl"
DEFAULT_JD_PATH = CHALLENGE_DATA_DIR / "job_description.docx"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "outputs" / "submission.csv"
DEFAULT_PRECOMPUTE_DIR = ROOT_DIR / "precompute"

CONSULTING_COMPANIES = {
    "TCS",
    "Infosys",
    "Wipro",
    "Accenture",
    "Cognizant",
    "Capgemini",
    "HCLTech",
    "Mindtree",
    "LTIMindtree",
    "Tech Mahindra",
    "Deloitte",
    "EY",
    "PwC",
    "KPMG",
}

CONSULTING_INDUSTRIES = {"IT Services", "Outsourcing", "BPO", "Staffing", "Consulting"}

PRODUCT_INDUSTRIES = {
    "Software",
    "Fintech",
    "E-commerce",
    "SaaS",
    "Internet",
    "HR Tech",
    "EdTech",
    "HealthTech",
    "Gaming",
}

PREFERRED_LOCATIONS = {
    "pune",
    "noida",
    "delhi",
    "gurgaon",
    "gurugram",
    "ncr",
    "hyderabad",
    "mumbai",
    "bangalore",
    "bengaluru",
}

AI_CORE_TERMS = {
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "deep learning",
    "nlp",
    "llm",
    "rag",
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "recommender",
    "embeddings",
    "sentence-transformers",
    "vector",
    "vector database",
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "faiss",
    "elasticsearch",
    "opensearch",
    "python",
    "pytorch",
    "tensorflow",
    "fine-tuning",
    "lora",
    "qlora",
    "feature engineering",
    "statistical modeling",
    "ab testing",
    "a/b testing",
    "ndcg",
    "mrr",
    "map",
}

TECHNICAL_TITLE_TERMS = {
    "ai engineer",
    "ml engineer",
    "machine learning engineer",
    "data scientist",
    "data engineer",
    "software engineer",
    "backend engineer",
    "platform engineer",
    "search engineer",
    "ranking engineer",
    "research engineer",
}

NON_FIT_TITLE_TERMS = {
    "marketing manager",
    "hr manager",
    "accountant",
    "sales executive",
    "customer support",
    "graphic designer",
    "civil engineer",
    "mechanical engineer",
    "operations manager",
    "content writer",
}
