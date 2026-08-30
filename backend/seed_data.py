"""
seed_data.py — Seeds the PathMind database with the "Become a Data Scientist" domain.
28 skill nodes, prerequisite DAG edges, and 2–4 resources per skill.
"""

from sqlalchemy.orm import Session
from models import Skill, SkillPrereq, Resource


def seed(db: Session):
    """Populate skills, prereqs, and resources. Called once on first startup."""

    # -----------------------------------------------------------------------
    # 1. Skills  (id assigned by order of insertion → auto-increment)
    # -----------------------------------------------------------------------
    skills_data = [
        # ── Programming Foundation ──────────────────────────────────────────
        {"name": "Python Basics",          "category": "Programming",  "difficulty": 1, "description": "Variables, data types, control flow, functions, and basic I/O in Python."},
        {"name": "Python Intermediate",    "category": "Programming",  "difficulty": 2, "description": "OOP, list comprehensions, file I/O, error handling, virtual environments, and pip."},
        {"name": "Git & Version Control",  "category": "Programming",  "difficulty": 1, "description": "git init/clone/commit/push/pull, branching, merging, GitHub collaboration."},
        {"name": "Command Line & Linux",   "category": "Programming",  "difficulty": 1, "description": "Shell navigation, file management, environment variables, bash scripting basics."},

        # ── Data Manipulation ────────────────────────────────────────────────
        {"name": "NumPy",                  "category": "Data Manipulation", "difficulty": 2, "description": "N-dimensional arrays, vectorised operations, broadcasting, and random number generation."},
        {"name": "Pandas",                 "category": "Data Manipulation", "difficulty": 2, "description": "DataFrames, Series, data cleaning, groupby, merge/join, and time-series handling."},
        {"name": "Data Cleaning",          "category": "Data Manipulation", "difficulty": 2, "description": "Handling missing values, outliers, data type coercion, and deduplication."},

        # ── Databases & SQL ──────────────────────────────────────────────────
        {"name": "SQL Fundamentals",       "category": "Databases",    "difficulty": 2, "description": "SELECT, WHERE, GROUP BY, JOINs, subqueries, and aggregate functions."},
        {"name": "Advanced SQL",           "category": "Databases",    "difficulty": 3, "description": "Window functions, CTEs, query optimisation, and database design principles."},

        # ── Mathematics ──────────────────────────────────────────────────────
        {"name": "Statistics Fundamentals","category": "Mathematics",  "difficulty": 2, "description": "Descriptive stats, probability distributions, hypothesis testing, p-values, and confidence intervals."},
        {"name": "Linear Algebra",         "category": "Mathematics",  "difficulty": 3, "description": "Vectors, matrices, eigenvalues, SVD — the mathematical backbone of ML algorithms."},
        {"name": "Calculus & Optimisation","category": "Mathematics",  "difficulty": 3, "description": "Derivatives, gradients, chain rule, gradient descent — essential for understanding how models learn."},

        # ── Data Visualisation ───────────────────────────────────────────────
        {"name": "Data Visualisation",     "category": "Visualization","difficulty": 2, "description": "Matplotlib, Seaborn, Plotly — creating charts, heatmaps, pair plots, and dashboards."},
        {"name": "Exploratory Data Analysis","category": "Visualization","difficulty": 2,"description": "EDA workflow: distributions, correlations, feature patterns, and storytelling with data."},

        # ── Machine Learning ─────────────────────────────────────────────────
        {"name": "ML Fundamentals",        "category": "Machine Learning","difficulty": 3,"description": "Supervised vs unsupervised, bias-variance tradeoff, train/val/test splits, evaluation metrics."},
        {"name": "Scikit-learn",           "category": "Machine Learning","difficulty": 3,"description": "Pipelines, preprocessing, cross-validation, regression, classification, and clustering with sklearn."},
        {"name": "Feature Engineering",    "category": "Machine Learning","difficulty": 3,"description": "Encoding, scaling, feature selection, polynomial features, and creating domain-specific features."},
        {"name": "Model Evaluation & Tuning","category": "Machine Learning","difficulty": 3,"description": "GridSearchCV, RandomizedSearchCV, learning curves, ROC/AUC, precision-recall, and hyperparameter tuning."},

        # ── Deep Learning ────────────────────────────────────────────────────
        {"name": "Deep Learning Basics",   "category": "Deep Learning","difficulty": 4,"description": "Neural network architecture, activation functions, backpropagation, and training loops."},
        {"name": "PyTorch / TensorFlow",   "category": "Deep Learning","difficulty": 4,"description": "Tensors, autograd, custom datasets, DataLoaders, model training with a major DL framework."},
        {"name": "CNNs & Computer Vision", "category": "Deep Learning","difficulty": 4,"description": "Convolutional layers, pooling, transfer learning with ResNet/VGG, and image classification projects."},
        {"name": "NLP & Transformers",     "category": "Deep Learning","difficulty": 5,"description": "Text preprocessing, embeddings, attention mechanism, BERT/GPT fine-tuning, and HuggingFace."},

        # ── MLOps & Deployment ───────────────────────────────────────────────
        {"name": "REST APIs & FastAPI",    "category": "MLOps",        "difficulty": 3,"description": "Building and consuming REST APIs, Pydantic models, async endpoints — essential for ML serving."},
        {"name": "Docker & Containers",    "category": "MLOps",        "difficulty": 3,"description": "Dockerfiles, images, containers, docker-compose, and containerising ML applications."},
        {"name": "Model Deployment",       "category": "MLOps",        "difficulty": 4,"description": "Serving ML models with FastAPI/Flask, cloud deployment (AWS/GCP/Azure), and latency optimisation."},
        {"name": "MLflow & Experiment Tracking","category": "MLOps",   "difficulty": 3,"description": "Logging metrics/artifacts, experiment comparison, model registry, and reproducibility."},
        {"name": "Cloud & Big Data Basics","category": "MLOps",        "difficulty": 4,"description": "S3, BigQuery, Spark basics, distributed data processing, and cloud ML services overview."},

        # ── Capstone ─────────────────────────────────────────────────────────
        {"name": "End-to-End DS Project",  "category": "Capstone",     "difficulty": 5,"description": "Full pipeline: data ingestion → EDA → modelling → evaluation → deployment → monitoring."},
    ]

    skill_objs = []
    for s in skills_data:
        skill = Skill(**s)
        db.add(skill)
        skill_objs.append(skill)
    db.flush()  # Get auto-generated IDs

    # Build a name→id map
    name_to_id = {s.name: s.id for s in skill_objs}

    # -----------------------------------------------------------------------
    # 2. Prerequisite Edges (prereq → skill)
    # -----------------------------------------------------------------------
    edges = [
        # Programming chain
        ("Python Basics",          "Python Intermediate"),
        ("Python Basics",          "NumPy"),
        ("Python Basics",          "Git & Version Control"),
        ("Python Basics",          "Command Line & Linux"),

        # Data manipulation
        ("Python Intermediate",    "NumPy"),
        ("NumPy",                  "Pandas"),
        ("Pandas",                 "Data Cleaning"),
        ("Pandas",                 "Exploratory Data Analysis"),
        ("Data Cleaning",          "Exploratory Data Analysis"),

        # SQL path
        ("Python Basics",          "SQL Fundamentals"),
        ("SQL Fundamentals",       "Advanced SQL"),

        # Math chain
        ("Statistics Fundamentals","ML Fundamentals"),
        ("Linear Algebra",         "ML Fundamentals"),
        ("Linear Algebra",         "Deep Learning Basics"),
        ("Calculus & Optimisation","Deep Learning Basics"),
        ("Statistics Fundamentals","Calculus & Optimisation"),

        # Visualization
        ("Pandas",                 "Data Visualisation"),
        ("Data Visualisation",     "Exploratory Data Analysis"),

        # ML chain
        ("Python Intermediate",    "Scikit-learn"),
        ("NumPy",                  "ML Fundamentals"),
        ("ML Fundamentals",        "Scikit-learn"),
        ("ML Fundamentals",        "Feature Engineering"),
        ("Scikit-learn",           "Feature Engineering"),
        ("Feature Engineering",    "Model Evaluation & Tuning"),
        ("Scikit-learn",           "Model Evaluation & Tuning"),

        # Deep Learning chain
        ("ML Fundamentals",        "Deep Learning Basics"),
        ("Deep Learning Basics",   "PyTorch / TensorFlow"),
        ("PyTorch / TensorFlow",   "CNNs & Computer Vision"),
        ("PyTorch / TensorFlow",   "NLP & Transformers"),

        # MLOps chain
        ("Python Intermediate",    "REST APIs & FastAPI"),
        ("Command Line & Linux",   "Docker & Containers"),
        ("REST APIs & FastAPI",    "Model Deployment"),
        ("Docker & Containers",    "Model Deployment"),
        ("Model Evaluation & Tuning","Model Deployment"),
        ("Scikit-learn",           "MLflow & Experiment Tracking"),
        ("Docker & Containers",    "Cloud & Big Data Basics"),
        ("Advanced SQL",           "Cloud & Big Data Basics"),

        # Capstone requires everything important
        ("Model Deployment",       "End-to-End DS Project"),
        ("Exploratory Data Analysis","End-to-End DS Project"),
        ("MLflow & Experiment Tracking","End-to-End DS Project"),
        ("Advanced SQL",           "End-to-End DS Project"),
    ]

    for prereq_name, skill_name in edges:
        p_id = name_to_id.get(prereq_name)
        s_id = name_to_id.get(skill_name)
        if p_id and s_id:
            db.add(SkillPrereq(skill_id=s_id, prereq_skill_id=p_id))

    db.flush()

    # -----------------------------------------------------------------------
    # 3. Resources (2–4 per skill)
    # -----------------------------------------------------------------------
    resources_data = [
        # Python Basics
        ("Python Basics", "Python for Everybody (Coursera)", "course", 1, "https://www.coursera.org/specializations/python", 20.0),
        ("Python Basics", "Official Python Tutorial", "article", 1, "https://docs.python.org/3/tutorial/", 5.0),
        ("Python Basics", "Automate the Boring Stuff with Python", "article", 1, "https://automatetheboringstuff.com/", 15.0),
        ("Python Basics", "Python Crash Course Project", "project", 1, "https://github.com/realpython/python-basics-exercises", 8.0),

        # Python Intermediate
        ("Python Intermediate", "Intermediate Python (Real Python)", "article", 2, "https://realpython.com/intermediate-python/", 10.0),
        ("Python Intermediate", "OOP in Python — Real Python", "article", 2, "https://realpython.com/python3-object-oriented-programming/", 5.0),
        ("Python Intermediate", "Python Packages & Virtual Envs", "video", 2, "https://www.youtube.com/watch?v=YYXdXT2l-Gg", 2.0),

        # Git & Version Control
        ("Git & Version Control", "Git & GitHub Crash Course (FCC)", "video", 1, "https://www.youtube.com/watch?v=RGOj5yH7evk", 1.5),
        ("Git & Version Control", "Pro Git Book (free)", "article", 1, "https://git-scm.com/book/en/v2", 8.0),
        ("Git & Version Control", "GitHub Learning Lab", "course", 1, "https://lab.github.com/", 4.0),

        # Command Line & Linux
        ("Command Line & Linux", "Linux Command Line Basics (Udacity)", "course", 1, "https://www.udacity.com/course/linux-command-line-basics--ud595", 5.0),
        ("Command Line & Linux", "The Linux Command Line Book", "article", 1, "https://linuxcommand.org/tlcl.php", 10.0),
        ("Command Line & Linux", "Bash Scripting Tutorial", "article", 1, "https://ryanstutorials.net/bash-scripting-tutorial/", 4.0),

        # NumPy
        ("NumPy", "NumPy Official Quickstart", "article", 2, "https://numpy.org/doc/stable/user/quickstart.html", 3.0),
        ("NumPy", "NumPy Tutorial — W3Schools", "article", 2, "https://www.w3schools.com/python/numpy/default.asp", 2.0),
        ("NumPy", "Scientific Python: NumPy (MIT)", "video", 2, "https://www.youtube.com/watch?v=DcfYgePyedM", 2.5),

        # Pandas
        ("Pandas", "Pandas Official Getting Started", "article", 2, "https://pandas.pydata.org/docs/getting_started/intro_tutorials/", 5.0),
        ("Pandas", "Kaggle Pandas Course (free)", "course", 2, "https://www.kaggle.com/learn/pandas", 4.0),
        ("Pandas", "Pandas Exercises (GitHub)", "project", 2, "https://github.com/guipsamora/pandas_exercises", 6.0),

        # Data Cleaning
        ("Data Cleaning", "Kaggle Data Cleaning Course", "course", 2, "https://www.kaggle.com/learn/data-cleaning", 4.0),
        ("Data Cleaning", "Handling Missing Data — Towards DS", "article", 2, "https://towardsdatascience.com/handling-missing-values-in-machine-learning-datasets", 1.5),
        ("Data Cleaning", "Real-World Data Cleaning Project", "project", 2, "https://www.kaggle.com/c/house-prices-advanced-regression-techniques/data", 5.0),

        # SQL Fundamentals
        ("SQL Fundamentals", "Mode Analytics SQL Tutorial", "course", 2, "https://mode.com/sql-tutorial/", 8.0),
        ("SQL Fundamentals", "SQLZoo", "course", 2, "https://sqlzoo.net/", 6.0),
        ("SQL Fundamentals", "SQL Murder Mystery", "project", 2, "https://mystery.knightlab.com/", 3.0),

        # Advanced SQL
        ("Advanced SQL", "Advanced SQL (Mode Analytics)", "course", 3, "https://mode.com/sql-tutorial/sql-window-functions/", 5.0),
        ("Advanced SQL", "LeetCode SQL Problems", "quiz", 3, "https://leetcode.com/problemset/database/", 10.0),
        ("Advanced SQL", "Use the Index, Luke!", "article", 3, "https://use-the-index-luke.com/", 6.0),

        # Statistics Fundamentals
        ("Statistics Fundamentals", "Statistics with Python (Coursera)", "course", 2, "https://www.coursera.org/specializations/statistics-with-python", 40.0),
        ("Statistics Fundamentals", "Khan Academy Statistics", "video", 2, "https://www.khanacademy.org/math/statistics-probability", 15.0),
        ("Statistics Fundamentals", "Think Stats (free book)", "article", 2, "https://greenteapress.com/wp/think-stats-2e/", 12.0),
        ("Statistics Fundamentals", "Statistical Tests Quiz", "quiz", 2, "https://www.khanacademy.org/math/statistics-probability/significance-tests-one-sample", 3.0),

        # Linear Algebra
        ("Linear Algebra", "Essence of Linear Algebra (3Blue1Brown)", "video", 3, "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab", 5.0),
        ("Linear Algebra", "Linear Algebra — MIT OpenCourseWare", "course", 3, "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/", 40.0),
        ("Linear Algebra", "Linear Algebra for ML (fast.ai)", "article", 3, "https://www.fast.ai/posts/2017-07-17-num-lin-alg.html", 8.0),

        # Calculus & Optimisation
        ("Calculus & Optimisation", "Calculus for ML (Khan Academy)", "video", 3, "https://www.khanacademy.org/math/calculus-1", 10.0),
        ("Calculus & Optimisation", "Gradient Descent from Scratch", "article", 3, "https://realpython.com/gradient-descent-algorithm-python/", 2.0),
        ("Calculus & Optimisation", "Matrix Calculus for DL (paper)", "article", 3, "https://arxiv.org/abs/1802.01528", 4.0),

        # Data Visualisation
        ("Data Visualisation", "Kaggle Data Visualization Course", "course", 2, "https://www.kaggle.com/learn/data-visualization", 4.0),
        ("Data Visualisation", "Matplotlib Official Tutorials", "article", 2, "https://matplotlib.org/stable/tutorials/", 4.0),
        ("Data Visualisation", "Plotly Express Gallery", "article", 2, "https://plotly.com/python/plotly-express/", 3.0),

        # Exploratory Data Analysis
        ("Exploratory Data Analysis", "EDA with Pandas Profiling", "article", 2, "https://towardsdatascience.com/exploratory-data-analysis-eda-a-practical-guide-and-template-for-structured-data-abfbf3ee3bd9", 2.5),
        ("Exploratory Data Analysis", "Kaggle EDA Project (Titanic)", "project", 2, "https://www.kaggle.com/code/startupsci/titanic-data-science-solutions", 4.0),
        ("Exploratory Data Analysis", "EDA with Python (Real Python)", "article", 2, "https://realpython.com/pandas-python-explore-dataset/", 2.0),

        # ML Fundamentals
        ("ML Fundamentals", "Andrew Ng ML Specialization (Coursera)", "course", 3, "https://www.coursera.org/specializations/machine-learning-introduction", 80.0),
        ("ML Fundamentals", "Hands-On ML with Scikit-Learn (Book)", "article", 3, "https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/", 40.0),
        ("ML Fundamentals", "ML Glossary", "article", 3, "https://ml-cheatsheet.readthedocs.io/", 3.0),
        ("ML Fundamentals", "ML Fundamentals Quiz", "quiz", 3, "https://www.kaggle.com/learn/intro-to-machine-learning", 4.0),

        # Scikit-learn
        ("Scikit-learn", "Scikit-learn Official Tutorials", "course", 3, "https://scikit-learn.org/stable/tutorial/index.html", 10.0),
        ("Scikit-learn", "Kaggle Intro to ML Course", "course", 3, "https://www.kaggle.com/learn/intro-to-machine-learning", 5.0),
        ("Scikit-learn", "Build a Complete ML Pipeline", "project", 3, "https://www.kaggle.com/competitions/titanic", 8.0),

        # Feature Engineering
        ("Feature Engineering", "Feature Engineering for ML (Udemy)", "course", 3, "https://www.udemy.com/course/feature-engineering-for-machine-learning/", 12.0),
        ("Feature Engineering", "Kaggle Feature Engineering Course", "course", 3, "https://www.kaggle.com/learn/feature-engineering", 5.0),
        ("Feature Engineering", "Feature Engineering Project", "project", 3, "https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques", 10.0),

        # Model Evaluation & Tuning
        ("Model Evaluation & Tuning", "Hyperparameter Tuning Guide (Towards DS)", "article", 3, "https://towardsdatascience.com/hyperparameter-tuning-the-random-forest-in-python-using-scikit-learn-28d2aa77dd74", 2.0),
        ("Model Evaluation & Tuning", "Cross-Validation Explained", "article", 3, "https://scikit-learn.org/stable/modules/cross_validation.html", 2.5),
        ("Model Evaluation & Tuning", "Optuna Hyperparameter Tutorial", "article", 3, "https://optuna.readthedocs.io/en/stable/tutorial/index.html", 4.0),
        ("Model Evaluation & Tuning", "Model Tuning Kaggle Challenge", "project", 3, "https://www.kaggle.com/competitions/playground-series-s3e1", 8.0),

        # Deep Learning Basics
        ("Deep Learning Basics", "Deep Learning Specialization (Coursera)", "course", 4, "https://www.coursera.org/specializations/deep-learning", 100.0),
        ("Deep Learning Basics", "Neural Networks from Scratch (book)", "article", 4, "https://nnfs.io/", 20.0),
        ("Deep Learning Basics", "3Blue1Brown Neural Networks", "video", 4, "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", 2.0),

        # PyTorch / TensorFlow
        ("PyTorch / TensorFlow", "PyTorch Official 60-min Blitz", "course", 4, "https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html", 3.0),
        ("PyTorch / TensorFlow", "fast.ai Practical Deep Learning", "course", 4, "https://course.fast.ai/", 30.0),
        ("PyTorch / TensorFlow", "Train a NN from Scratch Project", "project", 4, "https://github.com/karpathy/nn-zero-to-hero", 15.0),

        # CNNs & Computer Vision
        ("CNNs & Computer Vision", "CS231n Convolutional Neural Networks", "course", 4, "https://cs231n.github.io/", 40.0),
        ("CNNs & Computer Vision", "Transfer Learning Tutorial (PyTorch)", "article", 4, "https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html", 3.0),
        ("CNNs & Computer Vision", "Image Classification Kaggle Project", "project", 4, "https://www.kaggle.com/competitions/cifar-10", 10.0),

        # NLP & Transformers
        ("NLP & Transformers", "HuggingFace NLP Course (free)", "course", 5, "https://huggingface.co/learn/nlp-course/", 20.0),
        ("NLP & Transformers", "Attention Is All You Need (paper)", "article", 5, "https://arxiv.org/abs/1706.03762", 3.0),
        ("NLP & Transformers", "Sentiment Analysis Fine-tuning Project", "project", 5, "https://huggingface.co/docs/transformers/training", 8.0),

        # REST APIs & FastAPI
        ("REST APIs & FastAPI", "FastAPI Official Tutorial", "course", 3, "https://fastapi.tiangolo.com/tutorial/", 6.0),
        ("REST APIs & FastAPI", "Build a REST API with FastAPI", "project", 3, "https://testdriven.io/blog/fastapi-crud/", 5.0),
        ("REST APIs & FastAPI", "HTTP & REST Fundamentals", "article", 3, "https://restfulapi.net/", 2.0),

        # Docker & Containers
        ("Docker & Containers", "Docker Official Get Started", "course", 3, "https://docs.docker.com/get-started/", 4.0),
        ("Docker & Containers", "Docker for Data Scientists", "video", 3, "https://www.youtube.com/watch?v=0H2miBK_gAk", 1.5),
        ("Docker & Containers", "Containerise an ML App (Tutorial)", "project", 3, "https://testdriven.io/blog/docker-best-practices/", 4.0),

        # Model Deployment
        ("Model Deployment", "Deploy ML Model with FastAPI (Tutorial)", "article", 4, "https://towardsdatascience.com/how-to-deploy-a-machine-learning-model-with-fastapi-docker-and-github-actions-13374cbd638a", 3.0),
        ("Model Deployment", "Full ML Deployment Project", "project", 4, "https://github.com/DataTalksClub/mlops-zoomcamp", 20.0),
        ("Model Deployment", "BentoML: Simplify ML Serving", "course", 4, "https://docs.bentoml.com/en/latest/get-started/index.html", 5.0),

        # MLflow & Experiment Tracking
        ("MLflow & Experiment Tracking", "MLflow Official Tutorial", "course", 3, "https://mlflow.org/docs/latest/getting-started/intro-quickstart/index.html", 3.0),
        ("MLflow & Experiment Tracking", "Experiment Tracking with MLflow", "article", 3, "https://towardsdatascience.com/mlflow-part-1-getting-started-with-mlflow-8b45bfbbb334", 2.0),
        ("MLflow & Experiment Tracking", "MLOps Project with MLflow", "project", 3, "https://github.com/mlflow/mlflow/tree/master/examples", 6.0),

        # Cloud & Big Data Basics
        ("Cloud & Big Data Basics", "Google Cloud for ML (Coursera)", "course", 4, "https://www.coursera.org/learn/google-cloud-machine-learning-end-to-end-project", 15.0),
        ("Cloud & Big Data Basics", "Apache Spark Overview (Databricks)", "article", 4, "https://www.databricks.com/spark/about", 3.0),
        ("Cloud & Big Data Basics", "AWS SageMaker Getting Started", "course", 4, "https://aws.amazon.com/sagemaker/getting-started/", 8.0),

        # End-to-End DS Project
        ("End-to-End DS Project", "MLOps Zoomcamp (full course)", "course", 5, "https://github.com/DataTalksClub/mlops-zoomcamp", 40.0),
        ("End-to-End DS Project", "Kaggle Competition End-to-End", "project", 5, "https://www.kaggle.com/competitions", 30.0),
        ("End-to-End DS Project", "Full DS Portfolio Project Guide", "article", 5, "https://towardsdatascience.com/how-to-build-a-data-science-portfolio-5f566517c79c", 4.0),
        ("End-to-End DS Project", "DS Project Checklist", "quiz", 5, "https://github.com/ageron/handson-ml3/blob/main/ml_project_checklist.md", 2.0),
    ]

    for skill_name, title, rtype, difficulty, url, est_hours in resources_data:
        skill_id = name_to_id.get(skill_name)
        if skill_id:
            db.add(Resource(
                title=title,
                type=rtype,
                skill_id=skill_id,
                difficulty=difficulty,
                url=url,
                est_hours=est_hours,
            ))

    db.commit()
    print("[OK] Seed data loaded: 28 skills, prerequisite graph, and resources for 'Data Scientist' path.")
