from flask import Flask, request, jsonify, render_template
from itertools import combinations, chain
from collections import defaultdict
import csv
import io

app = Flask(__name__)

# Apriori functions
def find_frequent_1_itemsets(transactions, min_support):
    item_count = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            item_count[frozenset([item])] += 1
    return {itemset for itemset, count in item_count.items() if count >= min_support}

def apriori_gen(Lk_minus_1):
    candidates = set()
    itemsets = list(Lk_minus_1)
    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            l1, l2 = list(itemsets[i]), list(itemsets[j])
            if l1[:-1] == l2[:-1]:
                candidates.add(frozenset(l1 + [l2[-1]]))
    return candidates

def has_infrequent_subset(candidate, Lk_minus_1):
    k = len(candidate)
    subsets = combinations(candidate, k - 1)
    return any(frozenset(subset) not in Lk_minus_1 for subset in subsets)

def filter_candidates_by_support(candidates, transactions, min_support):
    item_count = defaultdict(int)
    for transaction in transactions:
        for candidate in candidates:
            if candidate.issubset(transaction):
                item_count[candidate] += 1
    return {itemset for itemset, count in item_count.items() if count >= min_support}

def apriori(transactions, min_support):
    L1 = find_frequent_1_itemsets(transactions, min_support)
    L = [L1]
    k = 2
    while True:
        candidates_k = apriori_gen(L[k - 2])
        candidates_k = {candidate for candidate in candidates_k if not has_infrequent_subset(candidate, L[k - 2])}
        Lk = filter_candidates_by_support(candidates_k, transactions, min_support)
        if not Lk:
            break
        L.append(Lk)
        k += 1
    return list(chain(*L))

# Route to display the HTML form
@app.route('/')
def index():
    return render_template('index.html')

# Route to process the uploaded CSV file
@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    min_support = int(request.form['min_support'])
    
    # Parse CSV file
    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.reader(stream)
    transactions = [row for row in csv_input]
    
    # Run Apriori algorithm
    result = apriori(transactions, min_support)
    result = [list(itemset) for itemset in result]
    return jsonify(result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)