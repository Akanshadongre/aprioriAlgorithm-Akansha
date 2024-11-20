import csv
import os
import time
from collections import defaultdict, Counter
from itertools import combinations
from flask import Flask, request, jsonify, render_template

# Initialize Flask app
app = Flask(__name__)

# Set up upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load transactions from a CSV file stream
def load_transactions(file_stream):
    """
    Reads transactions from a CSV file stream.
    """
    transactions = []
    file_stream.seek(0)  # Ensure the stream is at the beginning
    reader = csv.reader(file_stream.read().decode('utf-8').splitlines())
    for row in reader:
        transactions.append(set(row))
    return transactions

# Get frequent 1-itemsets
def get_frequent_1_itemsets(transactions, min_support):
    item_counts = Counter()
    for transaction in transactions:
        for item in transaction:
            item_counts[frozenset([item])] += 1
    return {itemset: count for itemset, count in item_counts.items() if count >= min_support}

# Generate candidate itemsets
def apriori_gen(itemsets, k):
    candidates = set()
    itemsets = list(itemsets)
    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            union_set = itemsets[i] | itemsets[j]
            if len(union_set) == k and not has_infrequent_subset(union_set, itemsets):
                candidates.add(union_set)
    return candidates

# Check for infrequent subsets
def has_infrequent_subset(candidate, frequent_itemsets):
    for subset in combinations(candidate, len(candidate) - 1):
        if frozenset(subset) not in frequent_itemsets:
            return True
    return False

# Filter candidates based on minimum support
def filter_candidates(transactions, candidates, min_support):
    item_counts = defaultdict(int)
    for transaction in transactions:
        for candidate in candidates:
            if candidate.issubset(transaction):
                item_counts[candidate] += 1
    return {itemset: count for itemset, count in item_counts.items() if count >= min_support}

# Apriori algorithm implementation
def apriori(transactions, min_support):
    frequent_itemsets = []
    current_itemsets = get_frequent_1_itemsets(transactions, min_support)
    k = 2
    while current_itemsets:
        frequent_itemsets.extend(current_itemsets.keys())
        candidates = apriori_gen(current_itemsets.keys(), k)
        current_itemsets = filter_candidates(transactions, candidates, min_support)
        k += 1
    return [set(itemset) for itemset in frequent_itemsets]

# Get maximal frequent itemsets
def get_maximal_frequent_itemsets(frequent_itemsets):
    maximal = []
    for itemset in sorted(frequent_itemsets, key=len, reverse=True):
        if not any(set(itemset).issubset(set(max_itemset)) for max_itemset in maximal):
            maximal.append(itemset)
    return maximal

# Home route
@app.route('/')
def index():
    return render_template('index.html')  # Render the form in index.html

# Process the uploaded CSV and run Apriori
@app.route('/run_apriori', methods=['POST'])
def run_apriori():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        min_support = int(request.form.get('min_support', 1))
        if min_support <= 0:
            raise ValueError("Minimal support must be greater than zero.")
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid minimal support value'}), 400

    try:
        transactions = load_transactions(file.stream)
        if not transactions:
            return jsonify({'error': 'The uploaded file contains no valid transactions'}), 400

        start_time = time.time()
        frequent_itemsets = apriori(transactions, min_support)
        maximal_frequent_itemsets = get_maximal_frequent_itemsets(frequent_itemsets)
        maximal_frequent_itemsets.sort(key=lambda x: (len(x), x))

        # Format the itemsets for output
        formatted_itemsets = [f"{{{','.join(map(str, itemset))}}}" for itemset in maximal_frequent_itemsets]
        end_time = time.time()

        response = {
            "Input file": file.filename,
            "Minimal support": min_support,
            "Maximal frequent itemsets": f"{{{','.join(formatted_itemsets)}}}",
            "End - total items": len(maximal_frequent_itemsets),
            "Total running time": f"{end_time - start_time:.6f} seconds"
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
