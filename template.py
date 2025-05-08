import os

# List of directories to create
directories = [
    "app",
    "app/core",
    "app/db",
    "app/routers",
    "app/schemas",
    "app/static",
    "app/static/uploads",
    "app/ai",
    "app/ai/models",
    "app/templates",
]

# Files to create with initial content
files_with_content = {
    # app/core
    "app/core/__init__.py": "",
    "app/core/config.py": "# Configuration settings (e.g., load from .env)\n",
    "app/core/security.py": "# Security utilities (password hashing, JWT)\n",
    # app/db
    "app/db/__init__.py": "",
    "app/db/engine.py": "# SQLAlchemy engine setup\n",
    "app/db/models.py": "# ORM model definitions\n",
    "app/db/crud.py": "# CRUD operations\n",
    # app/routers
    "app/routers/__init__.py": "",
    "app/routers/auth.py": "# Authentication routes\n",
    "app/routers/photo.py": "# Photo upload and retrieval routes\n",
    "app/routers/follow.py": "# Follow/unfollow routes\n",
    "app/routers/comment.py": "# Comment routes\n",
    "app/routers/rating.py": "# Rating routes\n",
    "app/routers/search.py": "# Search by tags routes\n",
    "app/routers/best_photo.py": "# Best photo of the day route\n",
    "app/routers/suggestion.py": "# Photographer suggestion route\n",
    "app/routers/analytics.py": "# Analytics dashboard route\n",
    "app/routers/admin.py": "# Admin panel routes\n",
    # app/schemas
    "app/schemas/__init__.py": "",
    "app/schemas/user.py": "# Pydantic schemas for user\n",
    "app/schemas/photo.py": "# Pydantic schemas for photo\n",
    "app/schemas/comment.py": "# Pydantic schemas for comment\n",
    "app/schemas/rating.py": "# Pydantic schemas for rating\n",
    "app/schemas/search.py": "# Pydantic schemas for search\n",
    "app/schemas/best_photo.py": "# Pydantic schemas for best photo\n",
    "app/schemas/suggestion.py": "# Pydantic schemas for suggestion\n",
    "app/schemas/analytics.py": "# Pydantic schemas for analytics\n",
    "app/schemas/admin.py": "# Pydantic schemas for admin\n",
    # app/ai
    "app/ai/__init__.py": "",
    "app/ai/predictor.py": "# AI predictor module for tags, etc.\n",
    "app/ai/models/README.md": "# AI models directory - place your model files here\n",
    # app/templates
    "app/templates/__init__.py": "",
    # Root files
    "create_tables.py": (
        "from app.db.models import Base\n"
        "from app.db.engine import engine\n\n"
        "if __name__ == '__main__':\n"
        "    Base.metadata.create_all(bind=engine)\n"
        "    print('Tables created successfully')\n"
    ),
    "requirements.txt": (
        "fastapi\n"
        "uvicorn\n"
        "SQLAlchemy\n"
        "mysql-connector-python\n"
        "passlib[bcrypt]\n"
        "python-jose\n"
        "pydantic\n"
        "python-multipart\n"
        "Pillow\n"
        "transformers\n"
        "torch\n"
    ),
    "README.md": (
        "# Photo Management App\n\n"
        "Project structure initialized. Fill in modules under 'app/'.\n"
    ),
    ".env": (
        "# Environment variables\n"
        "DATABASE_URL=mysql+mysqlconnector://username:password@localhost:3306/photo_app\n"
        "SECRET_KEY=your-secret-key\n"
    ),
}


def create_structure():
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Create files
    for filepath, content in files_with_content.items():
        # Ensure directory exists
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)

    print("✅ Project structure created successfully!")


if __name__ == '__main__':
    create_structure()
