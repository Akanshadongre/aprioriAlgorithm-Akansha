import csv
import time
from collections import defaultdict, Counter
from itertools import combinations
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def load_transactions(file_path):
    transactions = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            transactions.append(set(row))
    return transactions

def get_frequent_1_itemsets(transactions, min_support):
    item_counts = Counter()
    for transaction in transactions:
        for item in transaction:
            item_counts[frozenset([item])] += 1
    return {itemset: count for itemset, count in item_counts.items() if count >= min_support}

def apriori_gen(itemsets, k):
    candidates = set()
    itemsets = list(itemsets)
    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            union_set = itemsets[i] | itemsets[j]
            if len(union_set) == k and not has_infrequent_subset(union_set, itemsets):
                candidates.add(union_set)
    return candidates

def has_infrequent_subset(candidate, frequent_itemsets):
    for subset in combinations(candidate, len(candidate) - 1):
        if frozenset(subset) not in frequent_itemsets:
            return True
    return False

def filter_candidates(transactions, candidates, min_support):
    item_counts = defaultdict(int)
    for transaction in transactions:
        for candidate in candidates:
            if candidate.issubset(transaction):
                item_counts[candidate] += 1
    return {itemset: count for itemset, count in item_counts.items() if count >= min_support}

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

def get_maximal_frequent_itemsets(frequent_itemsets):
    maximal = []
    for itemset in sorted(frequent_itemsets, key=len, reverse=True):
        if not any(set(itemset).issubset(set(max_itemset)) for max_itemset in maximal):
            maximal.append(itemset)
    return maximal

@app.route('/')
def index():
    return render_template('index.html')  # Create an index.html file for the form

@app.route('/run_apriori', methods=['POST'])
def run_apriori():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    min_support = int(request.form.get('min_support', 1))

    file_path = f"./uploads/{file.filename}"
    file.save(file_path)

    try:
        transactions = load_transactions(file_path)
        start_time = time.time()
        frequent_itemsets = apriori(transactions, min_support)
        maximal_frequent_itemsets = get_maximal_frequent_itemsets(frequent_itemsets)
        maximal_frequent_itemsets.sort(key=lambda x: (len(x), x))

        # Format the itemsets as per your required output
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
