from pinecone import Pinecone
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
index_host = os.getenv("PINECONE_INDEX_HOST")

print(f"Connecting to Pinecone index at: {index_host}")
pc = Pinecone(api_key=api_key)
index = pc.Index(host=index_host)

namespace = "fraud-detection-csv"
vector_ids_file = "vector_ids.txt"

deleted = 0
not_found = 0
total = 0

print(f"Starting deletion process for namespace: {namespace}")
print(f"Reading vector IDs from: {vector_ids_file}")

with open(vector_ids_file, "r", encoding="utf-8") as f:
    for line in f:
        total += 1
        try:
            data = json.loads(line)
            vector_id = data.get("record_id")
            if vector_id:
                print(f"Attempting to delete vector ID: {vector_id}")
                index.delete(ids=[vector_id], namespace=namespace)
                deleted += 1
                print(f"Deleted: {vector_id}")
            else:
                print(f"No 'record_id' found in line {total}: {line.strip()}")
        except Exception as e:
            not_found += 1
            print(f"Error deleting vector at line {total}: {e}")

print(f"\nFinished deletion process.")
print(f"Total lines processed: {total}")
print(f"Vectors successfully deleted: {deleted}")
print(f"Errors (likely not found or malformed): {not_found}")