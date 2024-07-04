#!/bin/bash

# Create main directories
mkdir -p data/{raw,processed}
mkdir -p src/{data_ingestion,preprocessing,vector_db,agents,router,aggregator}
mkdir -p models/fine_tuned
mkdir -p configs
mkdir -p tests

# Create placeholder files
touch src/data_ingestion/twitter_fetcher.py
touch src/preprocessing/data_cleaner.py
touch src/vector_db/db_manager.py
touch src/agents/{engagement_classifier.py,sentiment_analyzer.py,topic_modeler.py,user_profiler.py}
touch src/router/query_router.py
touch src/aggregator/results_aggregator.py
touch configs/agent_configs.yaml
touch requirements.txt
touch README.md

echo "File structure created successfully!"