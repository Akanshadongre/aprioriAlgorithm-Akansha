from flask import Flask, request, jsonify, render_template
from itertools import combinations, chain
from collections import defaultdict,Counter
import csv
import io
import time

app = Flask(__name__)

def get_frequent_1_itemsets(transactions, min_support):
    item_counts = Counter()
    for transaction in transactions:
        for item in transaction:
            item_counts[frozenset([item])] += 1
    return {itemset: count for itemset, count in item_counts.items() if count >= min_support}

# Generate candidate itemsets of size k
def apriori_gen(itemsets, k):
    candidates = set()
    itemsets = list(itemsets)
    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            union_set = itemsets[i] | itemsets[j]
            if len(union_set) == k and not has_infrequent_subset(union_set, itemsets):
                candidates.add(union_set)
    return candidates

# Check if candidate has any infrequent subset
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
    return maximal  # Add this return statement

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/process_csv', methods=['POST'])
# def process_csv():
#     file = request.files['file']
#     min_support = int(request.form['min_support'])
#     # Parse CSV file
#     stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
#     csv_input = csv.reader(stream)
#     transactions = [row for row in csv_input]
#     # Measure execution time
#     start_time = time.time()
#     frequent_itemsets = apriori(transactions, min_support)
#     end_time = time.time()
#     execution_time = end_time - start_time
#     maximal_frequent_itemsets = get_maximal_frequent_itemsets(frequent_itemsets)
#     maximal_frequent_itemsets.sort(key=lambda x: (len(x), x))
#     # Calculate total count
#     total_count = len(maximal_frequent_itemsets)
#     # Format frequent itemsets output
#     formatted_output = [f"{{{','.join(map(str, itemset))}}}" for itemset in maximal_frequent_itemsets]
#     return jsonify({
#         "minimal_support": min_support,
#         "execution_time": f"{execution_time:.2f} seconds",
#         "total_count": total_count,
#         "result": formatted_output
#     })

@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    min_support = int(request.form['min_support'])
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    transactions = [set(row) for row in csv.reader(stream)]  # Convert to set directly
    
    start_time = time.time()
    frequent_itemsets = apriori(transactions, min_support)
    end_time = time.time()

    execution_time = end_time - start_time
    maximal_frequent_itemsets = get_maximal_frequent_itemsets(frequent_itemsets)
    maximal_frequent_itemsets.sort(key=lambda x: (len(x), x))
    total_count = len(maximal_frequent_itemsets)

    formatted_output = [f"{{{','.join(map(str,sorted(itemset))).strip()}}}" for itemset in maximal_frequent_itemsets]
    result_string = "{" + "".join(formatted_output) + "}"

    return render_template(
        'result.html', 
        minimal_support=min_support,
        execution_time=f"{execution_time:.2f} seconds",
        total_count=total_count,
        result=result_string
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
